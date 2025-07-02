from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction
from .forms import AlmaceneroForm, LoginForm, EmpresaForm, ProductoForm, LoteProductoForm
from .models import Almacenero, Empresa, PlanSuscripcion, SuscripcionUsuario, Producto, LoteProducto, MovimientoStock
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import plan_requerido, caracteristica_requerida
from django.contrib.auth import logout
from datetime import date, timedelta
from django.db.models import Q, Min, F, Sum, Count
from openpyxl import Workbook
from django.http import HttpResponse
from .utils import obtener_empresa_del_usuario
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
import time
import json

def vista_registro(request):
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST, prefix='almacenero')
        empresa_form = EmpresaForm(request.POST, prefix='empresa')

        # Comprueba si ambos formularios son válidos
        if almacenero_form.is_valid() and empresa_form.is_valid():
            try:
                with transaction.atomic():
                    # Lógica para crear el usuario, empresa, etc.
                    user = User.objects.create_user(
                        username=almacenero_form.cleaned_data['username'],
                        password=almacenero_form.cleaned_data['password']
                    )
                    empresa = empresa_form.save()
                    almacenero = almacenero_form.save(commit=False)
                    almacenero.usuario = user
                    almacenero.empresa = empresa
                    almacenero.save()

                    plan_gratuito = PlanSuscripcion.objects.get(nombre='FREE')
                    SuscripcionUsuario.objects.create(
                        empresa=empresa,
                        plan=plan_gratuito,
                        activa=True
                    )
                
                messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
                return redirect('login')
            
            except Exception as e:
                # Si algo falla durante la creación, muestra un error
                messages.error(request, f"Hubo un error inesperado durante el registro: {e}")
        
        else:
            # --- CORRECCIÓN CLAVE ---
            # Si los formularios NO son válidos, envía un mensaje de error general.
            # Django se encargará de mostrar los errores específicos en cada campo.
            messages.error(request, 'Por favor, corrige los errores en el formulario para continuar.')

    else:
        # Para una solicitud GET, simplemente crea formularios vacíos
        almacenero_form = AlmaceneroForm(prefix='almacenero')
        empresa_form = EmpresaForm(prefix='empresa')

    # Renderiza la plantilla, pasándole los formularios (que pueden contener errores si es POST)
    return render(request, 'inventario/registro.html', {
        'almacenero_form': almacenero_form,
        'empresa_form': empresa_form
    })

def vista_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
                return redirect('/home/')
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Por favor, complete los campos de inicio de sesión.")
    else:
        form = LoginForm()

    return render(request, 'inventario/login.html', {'form': form})

@login_required
def home(request):
    empresa = obtener_empresa_del_usuario(request.user)
    
    # --- CORRECCIÓN: Inicializamos el contexto con valores por defecto ---
    context = {
        'total_productos': 0,
        'stock_total': 0,
        'lotes_activos': 0,
        'dashboard_data_json': json.dumps({'labels': [], 'data': []})
    }

    if empresa:
        productos_empresa = Producto.objects.filter(empresa=empresa)
        
        # Si hay productos, calculamos las métricas reales
        if productos_empresa.exists():
            metricas = productos_empresa.aggregate(
                total_stock=Sum('lotes__cantidad'),
                total_lotes=Count('lotes')
            )
            
            stock_por_producto = (
                productos_empresa
                .annotate(stock=Sum('lotes__cantidad'))
                .filter(stock__gt=0)
                .values('nombre', 'stock')
                .order_by('-stock')[:10]
            )
            
            dashboard_data = {
                'labels': [item['nombre'] for item in stock_por_producto],
                'data': [item['stock'] for item in stock_por_producto],
            }
            
            # Actualizamos el contexto con los datos reales
            context.update({
                'total_productos': productos_empresa.count(),
                'stock_total': metricas.get('total_stock') or 0,
                'lotes_activos': metricas.get('total_lotes') or 0,
                'dashboard_data_json': json.dumps(dashboard_data)
            })

    return render(request, 'inventario/home.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('/')

@cache_page(60 * 5)
@vary_on_cookie
@login_required
def perfil(request):
    try:
        # ¡Todo en una sola consulta a la base de datos!
        suscripcion = SuscripcionUsuario.objects.select_related(
            'empresa__almacenero__usuario', 
            'plan'
        ).get(empresa__almacenero__usuario=request.user, activa=True)

        empresa = suscripcion.empresa
        almacenero = empresa.almacenero
        plan = suscripcion.plan

    except SuscripcionUsuario.DoesNotExist:
        # Manejo de casos donde el usuario no tiene suscripción activa
        # Esto es más limpio que múltiples try-except o condicionales
        almacenero = getattr(request.user, 'almacenero', None)
        empresa = almacenero.empresa if almacenero else None
        plan = None
        suscripcion = None
        messages.warning(request, "No tienes una suscripción activa.")

    context = {
        'almacenero': almacenero,
        'empresa': empresa,
        'plan': plan,
    }

    return render(request, 'inventario/perfil.html', context)

@login_required
def inventario_view(request):
    query = request.GET.get('q')

    # 1. Usa la función de ayuda para obtener la empresa de forma centralizada y segura.
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    # 2. Verifica si se encontró una empresa antes de continuar.
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        productos = Producto.objects.none() # Devuelve un QuerySet vacío
    else:
        # 3. Realiza la consulta principal a la base de datos.
        productos = (
            Producto.objects
            .filter(empresa=empresa_usuario)
            .annotate(
                # Calcula el stock sumando las cantidades de todos los lotes asociados.
                stock_total=Sum('lotes__cantidad'),
                # Encuentra la fecha de vencimiento más cercana entre todos los lotes.
                proximo_vencimiento=Min('lotes__fecha_vencimiento')
            )
        )

    # 4. Aplica el filtro de búsqueda si existe. Esta lógica ya era correcta.
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(marca__icontains=query) |
            Q(categoria__icontains=query)
        ).distinct()

        if not productos.exists():
            messages.info(request, f"No se encontraron productos que coincidan con '{query}'.")
        else:
            messages.success(request, f"Mostrando resultados para '{query}'.")

    # 5. Prepara el contexto para la plantilla.
    hoy = date.today()
    # Se calcula la fecha límite para el aviso de vencimiento (15 días desde hoy)
    hoy_mas_15dias = hoy + timedelta(days=15)

    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        # Se convierte a timestamp para poder compararlo fácilmente en JavaScript si es necesario.
        'hoy_mas_15dias': int(time.mktime(hoy_mas_15dias.timetuple())), 
    }
    
    return render(request, 'inventario/inventario.html', context)

@login_required
def agregar_producto(request):
    try:
        # Patrón optimizado: 1 consulta para obtener empresa y suscripción
        suscripcion = SuscripcionUsuario.objects.select_related('plan', 'empresa').get(
            empresa__almacenero__usuario=request.user, 
            activa=True
        )
        empresa_usuario = suscripcion.empresa
        plan = suscripcion.plan
    except SuscripcionUsuario.DoesNotExist:
        messages.error(request, "Tu cuenta no tiene una suscripción activa. No puedes agregar productos.")
        return redirect('home')

    # La lógica de verificación del límite de productos está bien
    productos_actuales = Producto.objects.filter(empresa=empresa_usuario).count()
    if plan.max_productos != 0 and productos_actuales >= plan.max_productos:
        messages.error(request, f"Has alcanzado el límite de productos para el plan '{plan.get_nombre_display()}' ({plan.max_productos} productos).")
        return redirect('inventario')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = empresa_usuario
            producto.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario')
    else:
        form = ProductoForm()

    return render(request, 'inventario/agregar-producto.html', {'form': form})

@login_required
def editar_producto(request, producto_id):
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes editar productos.")
        return redirect('inventario')

    # Solo permite editar productos de la empresa del usuario
    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario') # Usar el nombre de la URL aquí
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/editar-producto.html', {'form': form, 'producto': producto})

login_required
def editar_lote(request, lote_id):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # Ahora, get_object_or_404 busca un lote que cumpla AMBAS condiciones:
    # 1. Que tenga el id correcto.
    # 2. Que su producto asociado pertenezca a la empresa del usuario.
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)
    
    # El resto de la lógica no cambia, pero ahora es segura.
    if request.method == 'POST':
        form = LoteProductoForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote actualizado correctamente.")
            return redirect('detalle_producto', producto_id=lote.producto.id)
    else:
        # Pasamos la empresa al formulario para optimizarlo (ver siguiente sección)
        form = LoteProductoForm(instance=lote, empresa=empresa_usuario)

    return render(request, 'inventario/editar_lote.html', {'form': form, 'lote': lote})

@login_required
def retirar_lote(request, lote_id):
    # 1. Obtener la empresa del usuario de forma segura.
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # 2. Obtener el lote una sola vez, validando su pertenencia.
    lote = get_object_or_404(LoteProducto, id=lote_id, producto__empresa=empresa_usuario)

    if request.method == 'POST':
        try:
            cantidad_a_retirar = int(request.POST.get('cantidad', 0))
        except (ValueError, TypeError):
            messages.error(request, "La cantidad ingresada no es un número válido.")
            return redirect('detalle_producto', producto_id=lote.producto.id)

        # 3. Validar la cantidad sin hacer una consulta extra a la BD.
        if cantidad_a_retirar <= 0:
            messages.error(request, "La cantidad a retirar debe ser mayor que cero.")
            return redirect('detalle_producto', producto_id=lote.producto.id)

        try:
            with transaction.atomic():
                # 4. Bloquea la fila del lote para la actualización atómica.
                # Se vuelve a obtener el lote dentro de la transacción con el bloqueo.
                lote_para_actualizar = LoteProducto.objects.select_for_update().get(id=lote_id)

                if cantidad_a_retirar > lote_para_actualizar.cantidad:
                    messages.error(request, f"No puedes retirar más de {lote_para_actualizar.cantidad} unidades.")
                else:
                    # La base de datos realiza el cálculo de forma atómica.
                    lote_para_actualizar.cantidad = F('cantidad') - cantidad_a_retirar
                    lote_para_actualizar.save()
                    messages.success(request, f"Se retiraron {cantidad_a_retirar} unidades del lote.")
            
            return redirect('detalle_producto', producto_id=lote.producto.id)
            
        except LoteProducto.DoesNotExist:
            # Esto no debería ocurrir si el get_object_or_404 inicial funcionó, pero es una buena práctica.
            messages.error(request, "El lote que intentas modificar ya no existe.")
            return redirect('inventario')

    # Para solicitudes GET, simplemente renderiza la página de confirmación.
    return render(request, 'inventario/retirar_lote.html', {'lote': lote})

@login_required
def eliminar_producto(request, producto_id):
    # 1. Obtener la empresa del usuario de forma segura y centralizada.
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # 2. Búsqueda segura del producto, validando la pertenencia a la empresa.
    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)

    if request.method == 'POST':
        # Al eliminar el producto, la configuración `on_delete=models.CASCADE` en tus
        # modelos se encargará de eliminar todos los lotes y movimientos asociados.
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'El producto "{nombre_producto}" ha sido eliminado exitosamente.')
        return redirect('inventario')
    
    # 3. Obtener el lote más próximo a vencer (si existe) para el contexto.
    # Esta consulta es eficiente y solo se ejecuta para la solicitud GET.
    lote_proximo = producto.lotes.order_by('fecha_vencimiento').first()

    context = {
        'producto': producto,
        'lote': lote_proximo
    }
    
    return render(request, 'inventario/eliminar_producto_confirm.html', context)

@login_required
def agregar_lote_producto(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    if request.method == 'POST':
        # Pasamos la empresa al formulario para la validación
        form = LoteProductoForm(request.POST, empresa=empresa_usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Lote registrado correctamente.")
            return redirect('inventario')
    else:
        # Pasamos la empresa al formulario para filtrar el queryset inicial
        form = LoteProductoForm(empresa=empresa_usuario)

    return render(request, 'inventario/agregar_lote.html', {'form': form})

@login_required
def eliminar_lote(request, lote_id):
    # 1. Obtener la empresa del usuario de forma segura.
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # 2. Búsqueda segura del lote, validando la pertenencia a través del producto.
    lote = get_object_or_404(
        LoteProducto.objects.select_related('producto'), 
        id=lote_id, 
        producto__empresa=empresa_usuario
    )
    producto_id = lote.producto.id

    if request.method == 'POST':
        lote.delete()
        messages.success(request, "Lote eliminado correctamente.")
        # Redirigimos al detalle del producto al que pertenecía el lote.
        return redirect('detalle_producto', producto_id=producto_id)
    
    return render(request, 'inventario/eliminar_lote_confirm.html', {'lote': lote})

@login_required
def detalle_producto(request, producto_id):
    # Usamos la función de ayuda
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    # La consulta del producto ahora es más limpia
    producto = get_object_or_404(
        Producto.objects.prefetch_related('lotes'), 
        id=producto_id, 
        empresa=empresa_usuario
    )
    
    lotes = sorted(producto.lotes.all(), key=lambda lote: lote.fecha_vencimiento)

    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'lotes': lotes
    })

@cache_page(60 * 60)
def vista_planes(request):
    planes = PlanSuscripcion.objects.all().order_by('precio')
    context = {
        'planes': planes
    }
    return render(request, 'inventario/planes.html', context)

@login_required
def seleccionar_plan(request, plan_id):
    plan = get_object_or_404(PlanSuscripcion, id=plan_id)
    
    # 1. Usa la función de ayuda para obtener la empresa de forma segura y eficiente.
    empresa_usuario = obtener_empresa_del_usuario(request.user)

    # 2. Valida que la empresa exista antes de procesar la solicitud.
    if not empresa_usuario:
        messages.error(request, "No se pudo procesar tu solicitud al no encontrar una empresa asociada.")
        return redirect('vista_planes')

    if request.method == 'POST':
        # 3. Lógica de negocio para evitar la selección directa del plan gratuito.
        if plan.nombre == 'FREE':
            messages.warning(request, "No es posible seleccionar el plan gratuito directamente.")
            return redirect('vista_planes')

        # 4. Usa una transacción atómica para garantizar la integridad de los datos.
        try:
            with transaction.atomic():
                # Desactiva cualquier suscripción que esté actualmente activa para la empresa.
                SuscripcionUsuario.objects.filter(empresa=empresa_usuario, activa=True).update(activa=False)

                # Crea la nueva suscripción con el plan seleccionado.
                SuscripcionUsuario.objects.create(
                    empresa=empresa_usuario,
                    plan=plan,
                    fecha_inicio=date.today(),
                    fecha_fin=date.today() + timedelta(days=30), # Asume una duración de 30 días
                    activa=True
                )
            
            messages.success(request, f"¡Has seleccionado exitosamente el plan {plan.get_nombre_display()}!")
            return redirect('home') # Redirige al home tras el éxito
        
        except Exception as e:
            # Captura cualquier error inesperado durante la transacción.
            messages.error(request, f"Ocurrió un error al cambiar de plan: {e}")
            return redirect('vista_planes')

    # Si la solicitud no es POST, simplemente redirige a la página de planes.
    return redirect('vista_planes')

@cache_page(60 * 15)
@login_required
@plan_requerido('PREMIUM')
def vista_reportes_avanzados(request):
    return render(request, 'inventario/reportes_avanzados.html')

@cache_page(60 * 15)
@login_required
@caracteristica_requerida('soporte_prioritario')
def vista_soporte_premium(request):
    return render(request, 'inventario/soporte_premium.html')

@login_required
def historial_movimientos_view(request):
    # 1. Obtener la empresa del usuario de forma segura.
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    
    if not empresa_usuario:
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        movimientos = MovimientoStock.objects.none() # Devuelve un QuerySet vacío
    else:
        # 2. Filtrar los movimientos por la empresa del usuario.
        # Esto asegura que un usuario solo vea sus propios datos.
        movimientos = (
            MovimientoStock.objects
            .filter(producto__empresa=empresa_usuario)
            .select_related('producto', 'lote')
            .order_by('-fecha')
        )

    context = {
        'movimientos': movimientos
    }
    
    return render(request, 'inventario/historial_movimientos.html', context)

@login_required
def descargar_plantilla_ventas(request):
    empresa_usuario = obtener_empresa_del_usuario(request.user)
    if not empresa_usuario:
        messages.error(request, "No se pudo encontrar la empresa asociada a tu cuenta.")
        return redirect('home')

    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Ventas"
    ws.append(['sku', 'cantidad'])

    # Consulta eficiente que solo trae los datos necesarios.
    productos = Producto.objects.filter(empresa=empresa_usuario).only('sku')

    for producto in productos:
        ws.append([producto.sku, ''])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_ventas.xlsx'
    wb.save(response)
    return response