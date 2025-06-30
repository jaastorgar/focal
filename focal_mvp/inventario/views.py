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
from django.db.models import Q
from django.db.models import Min
from django.db import models
from django.shortcuts import render
from openpyxl import Workbook
from django.http import HttpResponse
import datetime
import time

def vista_registro(request):
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST, prefix='almacenero')
        empresa_form = EmpresaForm(request.POST, prefix='empresa')

        if almacenero_form.is_valid() and empresa_form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear el objeto User (usuario)
                    username = almacenero_form.cleaned_data['username']
                    password = almacenero_form.cleaned_data['password']
                    user = User.objects.create_user(username=username, password=password)

                    # 2. Guardar la empresa usando el formulario (ModelForm lo maneja)
                    empresa = empresa_form.save()

                    almacenero = almacenero_form.save(commit=False) 
                    almacenero.usuario = user       # Asocia el usuario creado
                    almacenero.empresa = empresa    # Asocia la empresa creada
                    
                    # CAMBIO AQUÍ: Añadir el campo 'correo' a la instancia del almacenero antes de guardarla
                    almacenero.correo = almacenero_form.cleaned_data['correo'] # <-- Campo correo añadido

                    almacenero.save()               # Guarda la instancia final del almacenero

                    # 4. Asignar suscripción gratuita por defecto
                    try:
                        plan_gratuito = PlanSuscripcion.objects.get(nombre='FREE')
                        SuscripcionUsuario.objects.create(
                            empresa=empresa,
                            plan=plan_gratuito,
                            activa=True
                        )
                    except PlanSuscripcion.DoesNotExist:
                        messages.error(request, "ERROR: El plan 'FREE' no se encontró. Contacte al administrador.")

                messages.success(request, 'Registro exitoso. ¡Ahora puedes iniciar sesión!')
                return redirect('/login/') # Redirige a la página de login
            except Exception as e:
                # Captura cualquier error durante la transacción y lo muestra al usuario
                messages.error(request, f"Hubo un error en el registro: {e}. Por favor, inténtelo de nuevo.")
        else:
            # Si uno de los formularios no es válido, los errores se mostrarán automáticamente en el template
            pass
    else:
        # Para solicitudes GET, crea formularios vacíos
        almacenero_form = AlmaceneroForm(prefix='almacenero')
        empresa_form = EmpresaForm(prefix='empresa')

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
    return render(request, 'inventario/home.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('/')

@login_required
def perfil(request):
    # Obtener el objeto Almacenero asociado al usuario logeado
    try:
        almacenero = request.user.almacenero
    except Almacenero.DoesNotExist:
        almacenero = None

    # Obtener los datos de la empresa asociada al almacenero
    empresa = almacenero.empresa if almacenero else None

    # Obtener los datos de la suscripción y el plan activo de la empresa
    suscripcion = None
    plan = None
    if empresa:
        suscripcion = SuscripcionUsuario.objects.filter(empresa=empresa, activa=True).first()
        if suscripcion:
            plan = suscripcion.plan

    context = {
        'almacenero': almacenero,
        'empresa': empresa,
        'plan': plan,
    }

    return render(request, 'inventario/perfil.html', context)

@login_required
def inventario_view(request):
    query = request.GET.get('q')

    try:
        empresa_usuario = request.user.almacenero.empresa
        productos = (
            Producto.objects
            .filter(empresa=empresa_usuario)
            .annotate(
                stock_total=models.Sum('lotes__cantidad'),
                proximo_vencimiento=Min('lotes__fecha_vencimiento')
            )
        )
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        productos = Producto.objects.none()

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

    hoy = date.today()
    hoy_mas_15dias = hoy + timedelta(days=15)

    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': int(time.mktime(hoy_mas_15dias.timetuple())),
    }
    return render(request, 'inventario/inventario.html', context)

@login_required
def agregar_producto(request):
    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes agregar productos.")
        return redirect('home') 

    # Obtener la suscripción activa de la empresa
    suscripcion = SuscripcionUsuario.objects.get(empresa=empresa_usuario, activa=True)
    plan = suscripcion.plan  # El plan de suscripción asociado a la empresa

    # Verificar el número de productos actuales de la empresa
    productos_actuales = Producto.objects.filter(empresa=empresa_usuario).count()

    if plan.max_productos != 0 and productos_actuales >= plan.max_productos:
        # Si el número de productos excede el límite, mostrar un mensaje de error
        messages.error(request, f"Has alcanzado el límite de productos para el plan '{plan.get_nombre_display()}' ({plan.max_productos} productos).")
        return redirect('inventario')  # O redirigir donde prefieras

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = empresa_usuario  # Asigna la empresa al producto
            producto.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario')  # Usar el nombre de la URL aquí
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

@login_required
def editar_lote(request, lote_id):
    lote = get_object_or_404(LoteProducto, id=lote_id)
    producto = lote.producto

    cantidad_original = lote.cantidad

    if request.method == 'POST':
        form = LoteProductoForm(request.POST, instance=lote)
        if form.is_valid():
            lote_actualizado = form.save(commit=False)
            diferencia = lote_actualizado.cantidad - cantidad_original
            lote_actualizado.save()
            messages.success(request, "Lote actualizado correctamente.")
            return redirect('detalle_producto', producto_id=producto.id)
    else:
        form = LoteProductoForm(instance=lote)

    return render(request, 'inventario/editar_lote.html', {'form': form, 'lote': lote})

@login_required
def retirar_lote(request, lote_id):
    lote = get_object_or_404(LoteProducto, id=lote_id)
    producto = lote.producto

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 0))
        if cantidad <= 0:
            messages.error(request, "La cantidad debe ser mayor a 0.")
        elif cantidad > lote.cantidad:
            messages.error(request, f"No puedes retirar más de {lote.cantidad} unidades.")
        else:
            lote.cantidad -= cantidad
            lote.save()
            messages.success(request, f"Se retiraron {cantidad} unidades del lote.")
            return redirect('detalle_producto', producto_id=producto.id)

    return render(request, 'inventario/retirar_lote.html', {'lote': lote})

@login_required
def eliminar_producto(request, producto_id):
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes eliminar productos.")
        return redirect('inventario')

    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)

    # Obtener el lote más próximo a vencer (si existe)
    lote_proximo = producto.lotes.order_by('fecha_vencimiento').first()

    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'El producto "{producto.nombre}" ha sido eliminado exitosamente.')
        return redirect('inventario')
    
    return render(request, 'inventario/eliminar_producto_confirm.html', {
        'producto': producto,
        'lote': lote_proximo  # 👈 este será usado en la plantilla
    })

@login_required
def agregar_lote_producto(request):
    if request.method == 'POST':
        form = LoteProductoForm(request.POST)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.save()  # Guardar directamente el lote
            messages.success(request, "Lote registrado correctamente.")
            return redirect('inventario')
    else:
        form = LoteProductoForm()

    return render(request, 'inventario/agregar_lote.html', {'form': form})

@login_required
def eliminar_lote(request, lote_id):
    lote = get_object_or_404(LoteProducto, id=lote_id)
    producto = lote.producto
    if request.method == 'POST':
        producto.stock = max(producto.stock - lote.cantidad, 0)
        producto.save()
        lote.delete()
        messages.success(request, "Lote eliminado y stock ajustado.")
        return redirect('detalle_producto', producto_id=producto.id)
    return render(request, 'inventario/eliminar_lote_confirm.html', {'lote': lote})

@login_required
def detalle_producto(request, producto_id):
    try:
        empresa_usuario = request.user.almacenero.empresa
        producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)
        lotes = producto.lotes.all().order_by('fecha_vencimiento')
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida.")
        return redirect('inventario')

    return render(request, 'inventario/detalle_producto.html', {
        'producto': producto,
        'lotes': lotes
    })

def vista_planes(request):
    planes = PlanSuscripcion.objects.all().order_by('precio')
    context = {
        'planes': planes
    }
    return render(request, 'inventario/planes.html', context)

@login_required
def seleccionar_plan(request, plan_id):
    plan = get_object_or_404(PlanSuscripcion, id=plan_id)

    try:
        empresa_usuario = request.user.almacenero.empresa
    except Almacenero.DoesNotExist:
        messages.error(request, "Tu cuenta no está asociada a una empresa. Contacta a soporte.")
        return redirect('vista_planes')

    if request.method == 'POST':
        if plan.nombre == 'FREE':
            messages.warning(request, "No es posible seleccionar el plan gratuito directamente de esta forma.")
            return redirect('vista_planes')

        # Desactivar suscripciones activas
        SuscripcionUsuario.objects.filter(empresa=empresa_usuario, activa=True).update(activa=False)

        # Crear nueva suscripción
        fecha_inicio = datetime.date.today()
        fecha_fin = fecha_inicio + datetime.timedelta(days=30)

        SuscripcionUsuario.objects.create(
            empresa=empresa_usuario,
            plan=plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activa=True
        )
        messages.success(request, f"¡Has seleccionado exitosamente el plan {plan.get_nombre_display()}!")
        return redirect('/home/')

    return redirect('vista_planes')

@login_required
@plan_requerido('PREMIUM')
def vista_reportes_avanzados(request):
    return render(request, 'inventario/reportes_avanzados.html')

@login_required
@caracteristica_requerida('soporte_prioritario')
def vista_soporte_premium(request):
    return render(request, 'inventario/soporte_premium.html')

@login_required
def historial_movimientos_view(request):
    movimientos = MovimientoStock.objects.select_related('producto', 'lote').order_by('-fecha')

    return render(request, 'inventario/historial_movimientos.html', {
        'movimientos': movimientos
    })

@login_required
def descargar_plantilla_ventas(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Ventas"

    # Encabezados
    ws.append(['sku', 'cantidad'])

    # Productos del usuario
    productos = Producto.objects.filter(empresa=request.user.almacenero.empresa)

    for producto in productos:
        ws.append([producto.sku, ''])  # Columna vacía para ventas

    # Respuesta HTTP con archivo .xlsx
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_ventas.xlsx'
    wb.save(response)
    return response