from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Producto, LoteProducto, OfertaProducto, Almacenero, Empresa
import re

# --- TUS FUNCIONES DE VALIDACIÓN ---
def validar_run_rut(run_rut):
    run_rut = str(run_rut).upper().strip()
    run_rut = re.sub(r'[\.-]', '', run_rut)
    if not run_rut or len(run_rut) < 2:
        return False
    cuerpo = run_rut[:-1]
    dv = run_rut[-1]
    if not cuerpo.isdigit():
        return False
    suma = 0
    multiplo = 2
    for d in reversed(cuerpo):
        suma += int(d) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
    dv_calculado = 11 - (suma % 11)
    if dv_calculado == 11:
        dv_esperado = '0'
    elif dv_calculado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(dv_calculado)
    return dv_esperado == dv

def validar_password_segura(password):
    if not (8 <= len(password) <= 12):
        return False, "La contraseña debe tener entre 8 y 12 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una minúscula."
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r"[_\W]", password):
        return False, "La contraseña debe contener al menos un carácter especial."
    return True, ""

# --- FORMULARIOS ACTUALIZADOS ---

class EmailLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(EmailLoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo Electrónico'
        self.fields['password'].label = 'Contraseña'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'tu_correo@correo.com'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})

class RegistroAlmaceneroForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Almacenero
        fields = (
            'nombre', 'snombre', 'apellido', 'sapellido', 'run', 
            'email', 'telefono', 'direccion', 'comuna', 'fecha_nacimiento'
        )
        
        # Widgets para placeholders y estilos
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Juan'}),
            'snombre': forms.TextInput(attrs={'placeholder': 'Ej: Pablo (opcional)'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej: Pérez'}),
            'sapellido': forms.TextInput(attrs={'placeholder': 'Ej: González (opcional)'}),
            'run': forms.TextInput(attrs={'placeholder': '12.345.678-9'}),
            'email': forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56912345678'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle Falsa 123'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].label = 'Primer Nombre'
        self.fields['apellido'].label = 'Apellido Paterno'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar Contraseña'
        self.fields['password2'].help_text = None 

        # Aplicamos clases de CSS a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['comuna'].widget.attrs['class'] = 'form-select'

    def clean_run(self):
        run = self.cleaned_data.get('run')
        return str(run).upper().strip().replace('.', '').replace('-', '')

    def clean_password2(self):
        password = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        # Primero, la validación de que las contraseñas coinciden (que hace el UserCreationForm)
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        # Luego, nuestra validación de seguridad sobre la contraseña
        es_valida, mensaje = validar_password_segura(password)
        if not es_valida:
            raise forms.ValidationError(mensaje)
        
        return password2

class EmpresaForm(forms.ModelForm):
    """
    Formulario para crear una Empresa.
    """
    class Meta:
        model = Empresa
        fields = [
            'nombre_almacen', 'rut', 'direccion_tributaria', 'comuna',
            'run_representante', 'inicio_actividades', 'nivel_venta_uf',
            'giro_negocio', 'tipo_sociedad'
        ]
        widgets = {
            'nombre_almacen': forms.TextInput(attrs={'placeholder': 'Nombre del Almacén'}),
            'rut': forms.TextInput(attrs={'placeholder': '76.123.456-K'}),
            'direccion_tributaria': forms.TextInput(attrs={'placeholder': 'Calle Falsa 123'}),
            'run_representante': forms.TextInput(attrs={'placeholder': '12.345.678-9'}),
            'inicio_actividades': forms.DateInput(attrs={'type': 'date'}),
            'nivel_venta_uf': forms.TextInput(attrs={'placeholder': 'Ej: 0 - 2.400 UF'}),
            'giro_negocio': forms.TextInput(attrs={'placeholder': 'Ej: Venta al por menor'}),
            'tipo_sociedad': forms.TextInput(attrs={'placeholder': 'Ej: SpA, EIRL, etc.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se aplican las clases de CSS a todos los campos
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.DateInput):
                 field.widget.attrs['class'] = 'form-control'
        self.fields['comuna'].widget.attrs['class'] = 'form-select'

class ProductoForm(forms.ModelForm):
    """
    Formulario para crear o actualizar los datos de un Producto.
    """
    class Meta:
        model = Producto
        exclude = ('empresas',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class OfertaProductoForm(forms.ModelForm):
    class Meta:
        model = OfertaProducto
        fields = ['precio_compra', 'precio_venta']

OfertaProductoFormSet = forms.modelformset_factory(
    OfertaProducto,
    form=OfertaProductoForm,
    extra=1,
    can_delete=False
)

class LoteProductoForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=OfertaProducto.objects.none(), 
        label="Producto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = LoteProducto
        # Se asegura que el campo 'producto' esté primero
        fields = ['producto', 'cantidad', 'fecha_vencimiento']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class ArchivoVentasForm(forms.Form):
    archivo_ventas = forms.FileField()