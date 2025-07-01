from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from .forms import ContactoForm

# ==============================================================================
# VISTAS DE LANDING OPTIMIZADAS
# ==============================================================================

# El decorador @cache_page guarda el resultado de la solicitud GET de esta vista
# en el caché por 15 minutos. Las solicitudes POST no se cachean.
# Esto hace que tu página de inicio cargue instantáneamente para la mayoría de los visitantes.
@cache_page(60 * 15)
def landing_page_view(request):
    form = ContactoForm()
    return render(request, 'landing/index.html', {'form': form})


# El decorador @require_POST asegura que esta vista solo pueda ser llamada
# mediante una solicitud POST. Si se intenta acceder por GET, devolverá un error 405
# (Method Not Allowed), lo cual es más seguro.
@require_POST
def contacto_submit_view(request):
    form = ContactoForm(request.POST)
    if form.is_valid():
        form.save()  # Guarda el mensaje en la base de datos
        messages.success(request, "¡Gracias por tu mensaje! Nos pondremos en contacto contigo pronto.")
    else:
        # En caso de error en el formulario, se muestra un mensaje genérico.
        # Podrías implementar una lógica más compleja aquí si quisieras mostrar
        # los errores específicos del formulario.
        messages.error(request, "Hubo un error al enviar tu mensaje. Por favor, revisa los datos e intenta nuevamente.")
    
    # Después de procesar el formulario (con éxito o error), siempre redirige
    # de vuelta a la página de inicio.
    return redirect('landing_page')