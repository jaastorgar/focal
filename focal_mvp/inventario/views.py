from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction
from .forms import AlmaceneroForm, LoginForm, EmpresaForm, ProductoForm, RetirarStockForm
from .models import Almacenero, Empresa, PlanSuscripcion, SuscripcionUsuario, Producto
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .decorators import plan_requerido, caracteristica_requerida
from django.contrib.auth import logout
from datetime import date, timedelta
from django.db.models import Q
import datetime

# Create your views here.
def vista_registro(request):
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST)
        empresa_form = EmpresaForm(request.POST) # Necesitarás crear este formulario

        if almacenero_form.is_valid() and empresa_form.is_valid():
            with transaction.atomic():
                # Crear usuario
                user = User.objects.create_user(
                    username=almacenero_form.cleaned_data['username'],
                    password=almacenero_form.cleaned_data['password']
                )

                # Crear empresa
                empresa = Empresa.objects.create(
                    nombre_almacen=empresa_form.cleaned_data['nombre_almacen'],
                    rut=empresa_form.cleaned_data['rut'],
                    direccion_tributaria=empresa_form.cleaned_data['direccion_tributaria'],
                    comuna=empresa_form.cleaned_data['comuna'],
                    run_representante=empresa_form.cleaned_data['run_representante'],
                    inicio_actividades=empresa_form.cleaned_data['inicio_actividades'],
                    nivel_venta_uf=empresa_form.cleaned_data['nivel_venta_uf'],
                    giro_negocio=empresa_form.cleaned_data['giro_negocio'],
                )

                # Crear perfil del almacenero y asociarlo a la empresa
                Almacenero.objects.create(
                    usuario=user,
                    nombre=almacenero_form.cleaned_data['nombre'],
                    snombre=almacenero_form.cleaned_data['snombre'],
                    apellido=almacenero_form.cleaned_data['apellido'],
                    sapellido=almacenero_form.cleaned_data['sapellido'],
                    run=almacenero_form.cleaned_data['run'],
                    telefono=almacenero_form.cleaned_data['telefono'],
                    direccion=almacenero_form.cleaned_data['direccion'],
                    comuna=almacenero_form.cleaned_data['comuna'],
                    fecha_nacimiento=almacenero_form.cleaned_data['fecha_nacimiento'],
                    empresa=empresa
                )

                # Asignar suscripción gratuita por defecto
                # Asegúrate de que el plan 'FREE' exista en tu base de datos
                try:
                    plan_gratuito = PlanSuscripcion.objects.get(nombre='FREE')
                    SuscripcionUsuario.objects.create(
                        empresa=empresa,
                        plan=plan_gratuito,
                        activa=True
                    )
                except PlanSuscripcion.DoesNotExist:
                    # Manejar el caso en que el plan gratuito no existe (ej. loggear error)
                    print("ERROR: El plan 'FREE' no se encontró en la base de datos. Asegúrate de crearlo en el admin.")
                    # Opcional: Podrías redirigir a una página de error o mostrar un mensaje.

            return redirect('/login/') # Redirigir al login tras registro exitoso
    else:
        almacenero_form = AlmaceneroForm()
        empresa_form = EmpresaForm()

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
                return redirect('/home/')
            else:
                form.add_error(None, "Usuario o contraseña incorrectos")
    else:
        form = LoginForm()

    return render(request, 'inventario/login.html', {'form': form})

@login_required
def home(request):
    return render(request, 'inventario/home.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def perfil(request):
    return render(request, 'perfil.html', {'user': request.user})

# Listar productos
@login_required
def inventario_view(request):
    query = request.GET.get('q')
    
    productos = Producto.objects.all()

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
    try:
        hoy_mas_15dias_timestamp = int(datetime.datetime.combine(hoy + timedelta(days=15), datetime.datetime.min.time()).timestamp())
    except AttributeError: 
        hoy_mas_15dias_timestamp = None 
    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': hoy_mas_15dias_timestamp,
    }
    return render(request, 'inventario/inventario.html', context)

# Registrar nuevo producto
@login_required
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario')
    else:
        form = ProductoForm()
    return render(request, 'inventario/agregar-producto.html', {'form': form})

# Editar producto existente
@login_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/editar-producto.html', {'form': form, 'producto': producto})

@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        return redirect('inventario_view')
    # Si es GET, se podría mostrar una página de confirmación de eliminación
    return render(request, 'inventario/eliminar_producto_confirm.html', {'producto': producto}) # Necesitarías crear este template


# Vista para retirar stock
@login_required
def retirar_stock_view(request):
    if request.method == 'POST':
        form = RetirarStockForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']

            if cantidad > producto.stock:
                messages.error(request, f'No hay suficiente stock para retirar. Stock actual: {producto.stock}.')
            else:
                producto.stock -= cantidad
                producto.save()
                messages.success(request, f'Se retiraron {cantidad} unidades de "{producto.nombre}". Stock actual: {producto.stock}.')
            return redirect('retirar_stock')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

    else:
        # Si se accede por GET, podemos intentar precargar el producto si se pasa un ID
        initial_data = {}
        producto_id = request.GET.get('producto')
        if producto_id:
            try:
                producto = Producto.objects.get(id=producto_id)
                initial_data['producto'] = producto.id
                messages.info(request, f'Producto "{producto.nombre}" seleccionado para retiro.')
            except Producto.DoesNotExist:
                messages.error(request, 'El producto especificado no existe.')
        form = RetirarStockForm(initial=initial_data)

    return render(request, 'inventario/retirar_stock.html', {'form': form})

@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'El producto "{producto.nombre}" ha sido eliminado exitosamente.')
        return redirect('inventario') 

    return render(request, 'inventario/eliminar_producto_confirm.html', {'producto': producto})

def vista_planes(request):
    planes = PlanSuscripcion.objects.all().order_by('precio')
    context = {
        'planes': planes
    }
    return render(request, 'inventario/planes.html', context)

@login_required
def seleccionar_plan(request, plan_id):
    plan = get_object_or_404(PlanSuscripcion, id=plan_id)

    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except Almacenero.DoesNotExist:
        messages.error(request, "Tu cuenta no está asociada a una empresa. Contacta a soporte.")
        return redirect('vista_planes')
    except Empresa.DoesNotExist:
        messages.error(request, "La empresa asociada a tu cuenta no existe. Contacta a soporte.")
        return redirect('vista_planes')

    if request.method == 'POST':
        if plan.nombre == 'FREE':
            messages.warning(request, "No es posible seleccionar el plan gratuito directamente de esta forma.")
            return redirect('vista_planes')

        # Lógica para planes de pago
        # En un escenario real, aquí integrarías con una pasarela de pago (Stripe, PayPal, Mercado Pago, etc.)
        # Después de un pago exitoso, actualizarías la suscripción del usuario.

        # *** SIMULACIÓN DE PAGO EXITOSO ***
        with transaction.atomic():
            # Desactivar suscripción actual de la empresa (si existe)
            SuscripcionUsuario.objects.filter(empresa=empresa_usuario, activa=True).update(activa=False)

            # Crear nueva suscripción
            fecha_inicio = datetime.date.today()
            # Ejemplo: Suscripción válida por 1 mes
            fecha_fin = fecha_inicio + datetime.timedelta(days=30) # O calcula según el período del plan

            SuscripcionUsuario.objects.create(
                empresa=empresa_usuario,
                plan=plan,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                activa=True
            )
            messages.success(request, f"¡Has seleccionado exitosamente el plan {plan.get_nombre_display()}!")
            return redirect('/home/') # O a una página de confirmación

    return redirect('vista_planes')

@login_required
@plan_requerido('PREMIUM')
def vista_reportes_avanzados(request):
    # Aquí iría la lógica para mostrar reportes avanzados
    return render(request, 'inventario/reportes_avanzados.html')

@login_required
@caracteristica_requerida('soporte_prioritario') # Solo usuarios con soporte prioritario pueden acceder
def vista_soporte_premium(request):
    # Aquí iría la lógica para la interfaz de soporte premium
    return render(request, 'inventario/soporte_premium.html')