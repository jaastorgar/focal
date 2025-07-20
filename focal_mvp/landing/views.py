from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from .forms import ContactoForm, LoginForm
from django.contrib.auth import login, authenticate
from inventario.forms import AlmaceneroForm, EmpresaForm
from inventario.models import PlanSuscripcion, SuscripcionUsuario


@cache_page(60 * 15)
def landing_page_view(request):
    form = ContactoForm()
    return render(request, 'landing/index.html', {'form': form})

@require_POST
def contacto_submit_view(request):
    form = ContactoForm(request.POST)
    if form.is_valid():
        form.save()  
        messages.success(request, "¡Gracias por tu mensaje! Nos pondremos en contacto contigo pronto.")
    else:
        messages.error(request, "Hubo un error al enviar tu mensaje. Por favor, revisa los datos e intenta nuevamente.")
        
    return redirect('landing')

def vista_registro(request):
    from django.contrib.auth.models import User
    from django.db import transaction
    
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST, prefix='almacenero')
        empresa_form = EmpresaForm(request.POST, prefix='empresa')

        if almacenero_form.is_valid() and empresa_form.is_valid():
            try:
                with transaction.atomic():
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
                messages.error(request, f"Hubo un error inesperado durante el registro: {e}")
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario para continuar.')

    else:
        almacenero_form = AlmaceneroForm(prefix='almacenero')
        empresa_form = EmpresaForm(prefix='empresa')

    return render(request, 'landing/registro.html', {
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

    return render(request, 'landing/login.html', {'form': form})

@cache_page(60 * 60)
def vista_planes(request):
    planes = PlanSuscripcion.objects.all().order_by('precio')
    context = {
        'planes': planes
    }
    return render(request, 'landing/planes.html', context)