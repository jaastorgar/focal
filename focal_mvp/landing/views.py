from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
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
    # 1) Elegir automáticamente el plan por defecto
    default_plan = (
        PlanSuscripcion.objects.filter(precio=0).order_by("id").first()
        or PlanSuscripcion.objects.order_by("precio", "id").first()
    )
    if not default_plan:
        messages.error(request, "No hay planes de suscripción configurados.")
        return redirect("home")

    if request.method == "POST":
        user_form = RegistroAlmaceneroForm(request.POST)
        empresa_form = EmpresaForm(request.POST)

        if user_form.is_valid() and empresa_form.is_valid():
            try:
                with transaction.atomic():
                    # 2) Crear empresa
                    empresa = empresa_form.save()

                    # 3) Crear usuario y asociarlo a la empresa
                    user = user_form.save(commit=False)
                    user.empresa = empresa
                    user.save()

                    # 4) Crear suscripción activa con el plan por defecto
                    SuscripcionUsuario.objects.create(
                        empresa=empresa,
                        plan=default_plan,
                        activa=True,
                    )

                # 5) Login y redirección
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, "¡Registro exitoso! Bienvenido a FOCAL.")
                return redirect("login")  # o la ruta que prefieras

            except Exception as e:
                messages.error(request, f"Ocurrió un error durante el registro: {e}")
    else:
        user_form = RegistroAlmaceneroForm()
        empresa_form = EmpresaForm()

    return render(
        request,
        "landing/registro.html",
        {
            "user_form": user_form,
            "empresa_form": empresa_form,
            "plan": default_plan,  # por si lo quieres mostrar en el template
        },
    )

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

@require_http_methods(["GET"])
def get_comunas(request):
    from django.http import JsonResponse
    from inventario.models import REGIONES_COMUNAS
    
    """
    Vista que recibe una región vía GET y devuelve las comunas correspondientes en formato JSON.
    Ejemplo: /get-comunas/?region=Valparaíso
    """
    region = request.GET.get('region', '').strip()

    if not region:
        return JsonResponse({'comunas': []}, status=400)

    comunas = REGIONES_COMUNAS.get(region, [])

    if not comunas:
        return JsonResponse({'comunas': []}, status=404)

    return JsonResponse({'comunas': comunas})

def quienes_somos_view(request):
    return render(request, "landing/quienes_somos.html")