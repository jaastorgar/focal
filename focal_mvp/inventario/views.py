from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction
from .forms import AlmaceneroForm, LoginForm, EmpresaForm, ProductoForm, RetirarStockForm
from .models import Almacenero, Empresa, PlanSuscripcion, SuscripcionUsuario, Producto
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import plan_requerido, caracteristica_requerida
from django.contrib.auth import logout
from datetime import date, timedelta
from django.db.models import Q
import datetime

def vista_registro(request):
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST)
        empresa_form = EmpresaForm(request.POST)

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
                    rut_empresa=empresa_form.cleaned_data['rut_empresa'], # Corregido: 'rut' a 'rut_empresa'
                    direccion_tributaria=empresa_form.cleaned_data['direccion_tributaria'],
                    comuna=empresa_form.cleaned_data['comuna'],
                    run_representante=empresa_form.cleaned_data['run_representante'],
                    inicio_actividades=empresa_form.cleaned_data['inicio_actividades'],
                    nivel_venta_uf=empresa_form.cleaned_data['nivel_venta_uf'],
                    giro_negocio=empresa_form.cleaned_data['giro_negocio'],
                    tipo_sociedad=empresa_form.cleaned_data['tipo_sociedad'],
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
            return redirect('/login/')
        else:
            # Si uno de los formularios no es válido, se mostrarán los errores en el template
            # No es necesario agregar mensajes explícitos aquí, Django se encarga
            pass
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
    # Esto asume que cada User tiene un Almacenero relacionado
    try:
        almacenero = request.user.almacenero
    except Almacenero.DoesNotExist:
        almacenero = None # O redirigir a una página de error si es mandatorio

    context = {
        'user': request.user,
        'almacenero': almacenero,
    }
    return render(request, 'perfil.html', context)

@login_required
def inventario_view(request):
    query = request.GET.get('q')
    
    # Asegúrate de que solo se vean los productos de la empresa del usuario
    try:
        empresa_usuario = request.user.almacenero.empresa
        productos = Producto.objects.filter(empresa=empresa_usuario)
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No se pueden mostrar productos.")
        productos = Producto.objects.none() # Devuelve un queryset vacío

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
    # No es necesario convertir a timestamp si solo se usa en el template para comparación de fechas
    # La comparación de objetos date directamente en Django templates es posible
    hoy_mas_15dias = hoy + timedelta(days=15) 
    
    context = {
        'productos': productos,
        'query': query,
        'today': hoy,
        'hoy_mas_15dias': hoy_mas_15dias,
    }
    return render(request, 'inventario/inventario.html', context)

@login_required
def agregar_producto(request):
    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes agregar productos.")
        return redirect('home') # O a otra página adecuada

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = empresa_usuario # Asigna la empresa al producto
            producto.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario') # Usar el nombre de la URL aquí
    else:
        form = ProductoForm()
    return render(request, 'inventario/agregar-producto.html', {'form': form})

@login_required
def editar_producto(request, producto_id):
    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes editar productos.")
        return redirect('home')

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
def eliminar_producto(request, producto_id):
    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes eliminar productos.")
        return redirect('home')

    # Solo permite eliminar productos de la empresa del usuario
    producto = get_object_or_404(Producto, id=producto_id, empresa=empresa_usuario)
    
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'El producto "{producto.nombre}" ha sido eliminado exitosamente.')
        return redirect('inventario') # Usar el nombre de la URL aquí
    
    return render(request, 'inventario/eliminar_producto_confirm.html', {'producto': producto})

@login_required
def retirar_stock_view(request):
    # Asegúrate de que el usuario logeado tenga una empresa asociada
    try:
        empresa_usuario = request.user.almacenero.empresa
    except (Almacenero.DoesNotExist, Empresa.DoesNotExist):
        messages.error(request, "Tu cuenta no está asociada a una empresa válida. No puedes retirar stock.")
        return redirect('home')

    if request.method == 'POST':
        form = RetirarStockForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']

            # Asegurarse de que el producto pertenezca a la empresa del usuario
            if producto.empresa != empresa_usuario:
                messages.error(request, "No tienes permiso para retirar stock de este producto.")
                return redirect('retirar_stock_view')

            if cantidad > producto.stock:
                messages.error(request, f'No hay suficiente stock para retirar. Stock actual: {producto.stock}.')
            else:
                producto.stock -= cantidad
                producto.save()
                messages.success(request, f'Se retiraron {cantidad} unidades de "{producto.nombre}". Stock actual: {producto.stock}.')
            return redirect('retirar_stock_view') # Usar el nombre de la URL aquí
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        initial_data = {}
        producto_id = request.GET.get('producto')
        if producto_id:
            try:
                # Solo precargar si el producto pertenece a la empresa del usuario
                producto = Producto.objects.get(id=producto_id, empresa=empresa_usuario)
                initial_data['producto'] = producto.id
                messages.info(request, f'Producto "{producto.nombre}" seleccionado para retiro.')
            except Producto.DoesNotExist:
                messages.error(request, 'El producto especificado no existe o no pertenece a tu empresa.')
        
        # Filtra los productos en el queryset del formulario para que solo muestre los de la empresa del usuario
        form = RetirarStockForm(initial=initial_data)
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_usuario).order_by('nombre')


    return render(request, 'inventario/retirar_stock.html', {'form': form})

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
    except Empresa.DoesNotExist:
        messages.error(request, "La empresa asociada a tu cuenta no existe. Contacta a soporte.")
        return redirect('vista_planes')

    if request.method == 'POST':
        if plan.nombre == 'FREE':
            messages.warning(request, "No es posible seleccionar el plan gratuito directamente de esta forma.")
            return redirect('vista_planes')

        with transaction.atomic():
            # Desactivar suscripción actual de la empresa (si existe)
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