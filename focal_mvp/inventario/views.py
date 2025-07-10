from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .forms import ProductoForm, LoteProductoForm, ArchivoVentasForm
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
from django.db import models
import pandas as pd
import time
import json

@login_required
def home(request):
    """
    Muestra un dashboard enfocado en alertas de vencimiento y bajo stock.
    """
    try:
        # Obtenemos el objeto Almacenero para el saludo personalizado.
        almacenero = Almacenero.objects.get(usuario=request.user)
    except Almacenero.DoesNotExist:
        almacenero = None

    empresa = obtener_empresa_del_usuario(request.user)
    
    alertas_vencimiento = []
    alertas_stock_bajo = []

    if empresa:
        # 1. Alerta de Vencimiento: Lotes que vencen en los próximos 30 días.
        fecha_limite_vencimiento = date.today() + timedelta(days=30)
        alertas_vencimiento = (
            LoteProducto.objects
            .filter(
                producto__empresa=empresa, 
                cantidad__gt=0, 
                fecha_vencimiento__gte=date.today(),
                fecha_vencimiento__lte=fecha_limite_vencimiento
            )
            .order_by('fecha_vencimiento')
            .select_related('producto')[:5] # Mostramos los 5 más urgentes
        )

        # 2. Alerta de Stock Bajo: Productos con stock total <= 5.
        alertas_stock_bajo = (
            Producto.objects
            .filter(empresa=empresa)
            .annotate(stock_total=Sum('lotes__cantidad'))
            .filter(stock_total__lte=5, stock_total__gt=0)
            .order_by('stock_total')[:5] # Mostramos los 5 con menos stock
        )

    context = {
        'almacenero': almacenero,
        'alertas_vencimiento': alertas_vencimiento,
        'alertas_stock_bajo': alertas_stock_bajo,
    }
    
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

@login_required
@transaction.atomic # Usamos una transacción para asegurar la integridad de los datos
def procesar_ventas_archivo(request):
    if request.method == 'POST':
        form = ArchivoVentasForm(request.POST, request.FILES)
        if form.is_valid():
            empresa_usuario = obtener_empresa_del_usuario(request.user)
            if not empresa_usuario:
                messages.error(request, "Tu cuenta no está asociada a una empresa.")
                return redirect('procesar_ventas_archivo')

            archivo = request.FILES['archivo_ventas']
            try:
                # Leemos el archivo excel o csv
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                else:
                    df = pd.read_excel(archivo)
            except Exception as e:
                messages.error(request, f"Error al leer el archivo: {e}")
                return redirect('procesar_ventas_archivo')

            errores = []
            sid = transaction.savepoint() # Creamos un punto de guardado

            for index, row in df.iterrows():
                try:
                    sku = str(row['sku']).strip()
                    cantidad_a_retirar = int(row['cantidad'])

                    if cantidad_a_retirar <= 0:
                        continue

                    # Buscamos el producto que pertenece a la empresa del usuario
                    producto = Producto.objects.get(sku=sku, empresa=empresa_usuario)
                    
                    lotes_disponibles = LoteProducto.objects.filter(
                        producto=producto, cantidad__gt=0
                    ).order_by('fecha_vencimiento')

                    cantidad_restante = cantidad_a_retirar
                    for lote in lotes_disponibles:
                        if cantidad_restante <= 0:
                            break
                        
                        retiro = min(lote.cantidad, cantidad_restante)
                        lote.cantidad = models.F('cantidad') - retiro
                        lote.save()

                        MovimientoStock.objects.create(
                            lote=lote,
                            producto=producto,
                            cantidad_retirada=retiro,
                            usuario=request.user,
                            nota=f"Descuento por archivo: {archivo.name}"
                        )
                        cantidad_restante -= retiro
                    
                    if cantidad_restante > 0:
                        errores.append(f"Fila {index + 2}: Stock insuficiente para SKU {sku}. Faltaron {cantidad_restante} unidades.")

                except Producto.DoesNotExist:
                    errores.append(f"Fila {index + 2}: Producto con SKU {sku} no encontrado.")
                except Exception as e:
                    errores.append(f"Fila {index + 2}: Error procesando SKU {sku}: {e}")

            if errores:
                transaction.savepoint_rollback(sid) # Revertimos si hubo errores
                for error in errores:
                    messages.error(request, error)
            else:
                transaction.savepoint_commit(sid) # Confirmamos si todo salió bien
                messages.success(request, "Archivo procesado y stock actualizado correctamente.")
            
            return redirect('inventario')
    else:
        form = ArchivoVentasForm()

    return render(request, 'inventario/procesar_ventas_archivo.html', {'form': form})