from django import forms
from .models import Contacto
from django.forms.widgets import TextInput, PasswordInput

class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre_completo', 'correo_electronico', 'mensaje']



class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=PasswordInput(attrs={'class': 'form-control'}))