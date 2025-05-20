from django import forms
from django.contrib.auth.models import User
from .models import Almacenero

class RegistroUsuarioForm(forms.ModelForm):
    username = forms.CharField(label="Nombre de usuario")
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    nombre = forms.CharField(label="Primer nombre")
    snombre = forms.CharField(label="Segundo nombre")
    apellido = forms.CharField(label="Apellido paterno")
    sapellido = forms.CharField(label="Apellido materno")
    run = forms.CharField(label="RUN")
    telefono = forms.CharField(required=False)
    direccion = forms.CharField(required=False)
    comuna = forms.CharField(required=False)
    fecha_nacimiento = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password')

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")
        return cleaned_data
    
class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)