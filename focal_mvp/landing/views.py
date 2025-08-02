from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate
from django.db import transaction
from inventario.forms import RegistroAlmaceneroForm, EmailLoginForm, EmpresaForm
from inventario.models import PlanSuscripcion, SuscripcionUsuario


@cache_page(60 * 15)
def landing_page_view(request):
    from .forms import ContactoForm
    
    form = ContactoForm()
    return render(request, 'landing/index.html', {'form': form})

@require_POST
def contacto_submit_view(request):
    from .forms import ContactoForm
    
    form = ContactoForm(request.POST)
    if form.is_valid():
        form.save()  
        messages.success(request, "¡Gracias por tu mensaje! Nos pondremos en contacto contigo pronto.")
    else:
        messages.error(request, "Hubo un error al enviar tu mensaje. Por favor, revisa los datos e intenta nuevamente.")
        
    return redirect('landing')

def vista_registro(request):
    plan_id = request.GET.get('plan')
    try:
        plan = get_object_or_404(PlanSuscripcion, id=plan_id)
    except (ValueError, TypeError):
        messages.error(request, "El plan seleccionado no es válido.")
        return redirect('planes')

    if request.method == 'POST':
        user_form = RegistroAlmaceneroForm(request.POST)
        empresa_form = EmpresaForm(request.POST)

        if user_form.is_valid() and empresa_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save()
                    empresa = empresa_form.save()
                    # Se asocia el Almacenero a la Empresa
                    empresa.almaceneros.add(user)

                    SuscripcionUsuario.objects.create(
                        empresa=empresa,
                        plan=plan,
                        activa=True
                    )
                
                # Se inicia sesión especificando el backend
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"¡Registro exitoso! Inicia Sesión.")
                return redirect('login')

            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado durante el registro: {e}")
    else:
        user_form = RegistroAlmaceneroForm()
        empresa_form = EmpresaForm()

    context = {
        'user_form': user_form,
        'empresa_form': empresa_form,
        'plan': plan
    }
    return render(request, 'landing/registro.html', context)

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect(request.GET.get('next', 'home'))
    else:
        form = EmailLoginForm()

    return render(request, 'landing/login.html', {'form': form})

@cache_page(60 * 60)
def vista_planes(request):
    planes = PlanSuscripcion.objects.all().order_by('precio')
    context = {
        'planes': planes
    }
    return render(request, 'landing/planes.html', context)