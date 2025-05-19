from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .forms import RegistroUsuarioForm, LoginForm
from .models import Almacenero

# Create your views here.
def vista_registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            # Crear usuario
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            # Crear perfil del almacenero
            Almacenero.objects.create(
                usuario=user,
                nombre=form.cleaned_data['nombre'],
                rut=form.cleaned_data['rut'],
                telefono=form.cleaned_data['telefono'],
                direccion=form.cleaned_data['direccion'],
                comuna=form.cleaned_data['comuna'],
                fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
            )
            # Redirigir al login tras registro exitoso
            return redirect('/login/')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'inventario/registro.html', {'form': form})


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