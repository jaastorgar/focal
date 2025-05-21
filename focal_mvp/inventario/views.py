from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.db import transaction

# Importa tus formularios actualizados
from .forms import AlmaceneroForm, EmpresaForm, LoginForm

# Create your views here.
def vista_registro(request):
    if request.method == 'POST':
        almacenero_form = AlmaceneroForm(request.POST)
        empresa_form = EmpresaForm(request.POST)

        # Usamos transaction.atomic para asegurar que ambas creaciones (Almacenero y Empresa)
        # se completen con éxito o que ninguna de ellas se guarde si hay un error en cualquiera.
        try:
            with transaction.atomic():
                if almacenero_form.is_valid() and empresa_form.is_valid():
                    # 1. Guardar la Empresa primero
                    empresa = empresa_form.save()

                    # 2. Guardar el Almacenero (que también crea el User)
                    almacenero = almacenero_form.save(commit=False)
                    almacenero.empresa = empresa # Asigna la empresa recién creada al almacenero
                    almacenero.save() # Guarda el almacenero con la relación a la empresa

                    # Redirigir al login tras registro exitoso
                    return redirect('/login/')
                else:
                    # Si alguno de los formularios no es válido, se re-renderiza con los errores
                    pass # La vista renderizará los errores automáticamente
        except Exception as e:
            # Aquí podrías loggear el error o añadir un mensaje global al formulario
            print(f"Error durante el registro: {e}")
            almacenero_form.add_error(None, "Hubo un error en el registro. Por favor, inténtalo de nuevo.")

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