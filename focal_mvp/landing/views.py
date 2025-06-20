from django.shortcuts import render, redirect
from .forms import ContactoForm
from django.contrib import messages

# Create your views here.
def landing_page(request):
    return render(request, 'landing/index.html')

def contacto_view(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda el mensaje en la base de datos
            messages.success(request, "¡Gracias por tu mensaje! Nos pondremos en contacto contigo pronto.")
            return redirect('landing')  # Redirige a la página de inicio o la que quieras
        else:
            messages.error(request, "Hubo un error al enviar tu mensaje. Por favor, intenta nuevamente.")
    else:
        form = ContactoForm()
    
    return render(request, 'landing/index.html', {'form': form})