# inventario/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Producto, LoteProducto, OfertaProducto, Almacenero, Empresa, Proveedor, REGIONES_COMUNAS
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
            'nombres', 'apellidos', 'run','email', 'telefono', 
            'direccion', 'region', 'comuna', 'fecha_nacimiento'
        )
        widgets = {
            'nombres': forms.TextInput(attrs={'placeholder': 'Escribe tus nombres'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'Escribe tus apellidos'}),
            'run': forms.TextInput(attrs={'placeholder': '12.345.678-9'}),
            'email': forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56912345678'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle Falsa 123'}),
            'region': forms.Select(attrs={'class': 'form-select', 'id': 'id_region'}),
            'comuna': forms.Select(attrs={'class': 'form-select', 'id': 'id_comuna'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Etiquetas
        self.fields['nombres'].label = 'Nombres'
        self.fields['apellidos'].label = 'Apellidos'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar Contraseña'
        self.fields['password2'].help_text = None

        # Clases CSS para campos de texto
        for field_name, field in self.fields.items():
            if field_name not in ['region', 'comuna']:
                field.widget.attrs['class'] = 'form-control'

        # Opciones de región
        self.fields['region'].choices = [('', 'Seleccione la región')] + [(r, r) for r in REGIONES_COMUNAS.keys()]

        # Inicialmente, comunas vacías o todas si no hay región
        if not self.data.get('region'):
            self.fields['comuna'].choices = [('', 'Primero seleccione una región')]
        else:
            region = self.data.get('region')
            comunas = REGIONES_COMUNAS.get(region, [])
            self.fields['comuna'].choices = [('', 'Seleccione la comuna')] + list(comunas)

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        comuna = cleaned_data.get('comuna')

        if region and comuna:
            if comuna not in dict(REGIONES_COMUNAS.get(region, [])):
                raise forms.ValidationError("La comuna seleccionada no pertenece a la región elegida.")
        elif region and not comuna:
            raise forms.ValidationError("Debe seleccionar una comuna de la región elegida.")
        return cleaned_data 

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre_almacen', 'razon_social', 'rut', 'direccion_tributaria', 'region', 'comuna',
            'run_representante', 'inicio_actividades', 'nivel_venta_uf',
            'giro_negocio', 'tipo_sociedad'
        ]
        widgets = {
            'nombre_almacen': forms.TextInput(attrs={'placeholder': 'Nombre del Almacén'}),
            'razon_social': forms.TextInput(attrs={'placeholder': 'Razón Social'}),
            'rut': forms.TextInput(attrs={'placeholder': '76.123.456-K'}),
            'direccion_tributaria': forms.TextInput(attrs={'placeholder': 'Calle Falsa 123'}),
            'region': forms.Select(attrs={'class': 'form-select', 'id': 'id_region'}),
            'comuna': forms.Select(attrs={'class': 'form-select', 'id': 'id_comuna'}),
            'run_representante': forms.TextInput(attrs={'placeholder': '12.345.678-9'}),
            'inicio_actividades': forms.DateInput(attrs={'type': 'date'}),
            'nivel_venta_uf': forms.TextInput(attrs={'placeholder': 'Ej: 0 - 2.400 UF'}),
            'giro_negocio': forms.TextInput(attrs={'placeholder': 'Ej: Venta al por menor'}),
            'tipo_sociedad': forms.TextInput(attrs={'placeholder': 'Ej: SpA, EIRL, etc.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['region', 'comuna']:
                field.widget.attrs['class'] = 'form-control'

        # Cargar regiones
        self.fields['region'].choices = [('', 'Seleccione la región')] + [(r, r) for r in REGIONES_COMUNAS.keys()]

        # Cargar comunas según región (para edición)
        if not self.data.get('region'):
            self.fields['comuna'].choices = [('', 'Primero seleccione una región')]
        else:
            region = self.data.get('region')
            comunas = REGIONES_COMUNAS.get(region, [])
            self.fields['comuna'].choices = [('', 'Seleccione la comuna')] + list(comunas)

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        comuna = cleaned_data.get('comuna')

        if region and comuna:
            if comuna not in dict(REGIONES_COMUNAS.get(region, [])):
                raise forms.ValidationError("La comuna seleccionada no pertenece a la región elegida.")
        elif region and not comuna:
            raise forms.ValidationError("Debe seleccionar una comuna de la región.")
        return cleaned_data

class ProductoForm(forms.ModelForm):
    """
    Formulario para crear o actualizar los datos de un Producto.
    """
    class Meta:
        model = Producto
        exclude = ('empresas',)

    def __init__(self, *args, **kwargs):
        # Permitir pasar la empresa actual para validaciones
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_sku(self):
        from django.core.exceptions import ValidationError
        
        sku = self.cleaned_data.get('sku')
        if self.empresa and sku:
            # Buscar si ya existe una OfertaProducto con este sku para esta empresa
            if OfertaProducto.objects.filter(
                producto__sku=sku,
                empresa=self.empresa
            ).exists():
                raise ValidationError("Este SKU ya existe en tu inventario.")
        return sku

class OfertaProductoForm(forms.ModelForm):
    class Meta:
        model = OfertaProducto
        fields = ['precio_venta_base']

# Actualiza también el formset para usar el formulario corregido
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
        exclude = ['precio_compra', 'precio_venta'] 
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Permitir pasar la empresa del usuario para filtrar productos/ofertas
        self.empresa_usuario = kwargs.pop('empresa_usuario', None)
        super().__init__(*args, **kwargs)
        
        # Si se pasó la empresa, filtrar el queryset de productos/ofertas
        if self.empresa_usuario:
            ofertas_qs = OfertaProducto.objects.filter(empresa=self.empresa_usuario).select_related('producto')
            self.fields['producto'].queryset = ofertas_qs
        
        # Asegurarse de que los campos restantes tengan las clases correctas
        for field_name, field in self.fields.items():
            # Los Select ya tienen su clase en widgets
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

class ArchivoVentasForm(forms.Form):
    archivo_ventas = forms.FileField()
    
class ProveedorForm(forms.ModelForm):
    """
    Formulario para crear o actualizar un Proveedor.
    """
    class Meta:
        model = Proveedor
        # Excluye campos que se gestionan automáticamente o que quizás no quieras aquí
        exclude = ['creado', 'modificado'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proveedor'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón social completa'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del contacto principal'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contacto@proveedor.cl'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección del proveedor'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Los widgets ya tienen sus clases, pero por si acaso...
            if 'class' not in field.widget.attrs and not isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                 field.widget.attrs['class'] = 'form-control'