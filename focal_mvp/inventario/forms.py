from django import forms
from django.contrib.auth.models import User
from .models import Almacenero, Empresa # Asegúrate de importar Empresa

# Clase para aplicar 'form-control' a los widgets
class BootstrapFormMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif 'class' not in field.widget.attrs:
                 field.widget.attrs.update({'class': 'form-control'})

class AlmaceneroForm(BootstrapFormMixin, forms.ModelForm): # Usa el Mixin
    username = forms.CharField(label="Nombre de Usuario", max_length=150, help_text="Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_.")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Almacenero
        fields = [
            'username', 'password', 'confirm_password', 
            'nombre', 'snombre', 'apellido', 'sapellido',
            'run', 'telefono', 'direccion', 'comuna', 'fecha_nacimiento'
        ]
        # Si quieres que ciertos campos de Almacenero usen widgets específicos:
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'username': "Nombre de Usuario",
            'nombre': "Primer Nombre",
            'snombre': "Segundo Nombre",
            'apellido': "Apellido Paterno",
            'sapellido': "Apellido Materno",
            'run': "RUN",
            'telefono': "Teléfono",
            'direccion': "Dirección Personal",
            'comuna': "Comuna Personal",
            'fecha_nacimiento': "Fecha de Nacimiento",
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_run(self):
        run = self.cleaned_data['run']
        if Almacenero.objects.filter(run=run).exists():
            raise forms.ValidationError("Este RUN ya está registrado.")
        return run

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        almacenero = super().save(commit=False)
        almacenero.usuario = user
        if commit:
            almacenero.save()
        return almacenero


class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre_almacen', 'rut', 'direccion_tributaria', 'comuna',
            'run_representante', 'inicio_actividades', 'nivel_venta_uf',
            'giro_negocio', 'tipo_sociedad',
        ]
        widgets = {
            'inicio_actividades': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'nombre_almacen': "Nombre del Almacén/Empresa",
            'rut': "RUT de la Empresa",
            'direccion_tributaria': "Dirección Tributaria",
            'comuna': "Comuna de la Empresa",
            'run_representante': "RUN del Representante Legal",
            'inicio_actividades': "Fecha de Inicio de Actividades",
            'nivel_venta_uf': "Nivel de Ventas (UF)",
            'giro_negocio': "Giro de Negocio",
            'tipo_sociedad': "Tipo de Sociedad",
        }

class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))