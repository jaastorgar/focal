import re
from django import forms
from django.contrib.auth.models import User
from .models import Empresa, Producto, Contacto, LoteProducto
from django.forms.widgets import DateInput, TextInput, Textarea, Select, EmailInput, NumberInput, PasswordInput, CheckboxInput


# Validación de RUN/RUT
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

# Validación personalizada para contraseñas seguras
def validar_password_segura(password):
    if not (8 <= len(password) <= 12):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[_\W]", password):
        return False
    return True

class BootstrapFormMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (TextInput, Textarea, Select, EmailInput, NumberInput, PasswordInput, DateInput)):
                field.widget.attrs.setdefault('class', 'form-control')
            elif isinstance(field.widget, CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')

class AlmaceneroForm(BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(label="Nombre de usuario", widget=forms.TextInput(attrs={'placeholder': 'Ej: focal'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}))
    confirm_password = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={'placeholder': 'Repita su contraseña'}))

    nombre = forms.CharField(label="Primer nombre")
    snombre = forms.CharField(label="Segundo nombre", required=False)
    apellido = forms.CharField(label="Apellido paterno")
    sapellido = forms.CharField(label="Apellido materno")
    run = forms.CharField(label="RUN (sin puntos ni guion)", widget=forms.TextInput(attrs={'placeholder': 'Ej: 123456789'}))
    telefono = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={'placeholder': 'Ej: +56912345678'}))
    direccion = forms.CharField(label="Dirección", required=False)
    comuna = forms.CharField(label="Comuna", required=False)
    fecha_nacimiento = forms.DateField(label="Fecha de nacimiento", required=False, widget=DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password')

    def clean_run(self):
        run = self.cleaned_data['run']
        run_limpio = re.sub(r'[\.-]', '', run).upper().strip()
        if not validar_run_rut(run_limpio):
            raise forms.ValidationError("El RUN es inválido.")
        return run_limpio

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2:
            if p1 != p2:
                self.add_error("confirm_password", "Las contraseñas no coinciden.")
            elif not validar_password_segura(p1):
                self.add_error("password", "La contraseña debe tener entre 8 y 12 caracteres, incluyendo al menos una mayúscula, una minúscula, un número y un símbolo.")
        return cleaned_data

class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre_almacen', 'rut', 'direccion_tributaria', 'comuna',
            'run_representante', 'inicio_actividades', 'nivel_venta_uf',
            'giro_negocio', 'tipo_sociedad',
        ]
        widgets = {
            'inicio_actividades': DateInput(attrs={'type': 'date'}),
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

    # Validación para el campo 'run_representante' del EmpresaForm
    def clean_run_representante(self):
        run = self.cleaned_data['run_representante']
        run_limpio = re.sub(r'[\.-]', '', run).upper().strip()

        if not validar_run_rut(run_limpio):
            raise forms.ValidationError("El RUN del representante es inválido. Por favor, verifique el formato y el dígito verificador.")
        
        return run_limpio

    # Validación para el campo 'rut_empresa' del EmpresaForm
    def clean_rut_empresa(self):
        rut = self.cleaned_data['rut_empresa']
        rut_limpio = re.sub(r'[\.-]', '', rut).upper().strip()

        if not validar_run_rut(rut_limpio):
            raise forms.ValidationError("El RUT de la empresa es inválido. Por favor, verifique el formato y el dígito verificador.")
        
        return rut_limpio

class LoginForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=PasswordInput(attrs={'class': 'form-control'}))

class ProductoForm(BootstrapFormMixin, forms.ModelForm): # Ahora hereda de BootstrapFormMixin
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'sku',
            'marca',
            'categoria',
            'cantidad',
            'unidad_medida',
            'precio_compra',
            'precio_venta',
        ]
        widgets = {
            'fecha_vencimiento': DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'sku': 'Sku (Código Único)',
            'marca': 'Marca',
            'categoria': 'Categoría',
            'cantidad': 'Cantidad',
            'unidad_medida': 'Unidad de Medida',
            'precio_compra': 'Precio de Compra',
            'precio_venta': 'Precio de Venta',
        }
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0: # Añadido 'is not None' para evitar error si el campo está vacío
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock

    def clean_precio_venta(self):
        precio = self.cleaned_data.get('precio_venta')
        if precio is not None and precio < 0: # Añadido 'is not None'
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio
    
class RetirarStockForm(forms.Form): 
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all().order_by('nombre'),
        label="Seleccionar Producto",
        empty_label="--- Seleccione un producto ---",
        widget=Select(attrs={'class': 'form-control'})
    )
    
    cantidad = forms.IntegerField(
        label="Cantidad a Retirar",
        min_value=1,
        widget=NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if producto and cantidad:
            if cantidad > producto.stock:
                self.add_error('cantidad', f'No hay suficiente stock. Solo quedan {producto.stock} unidades de {producto.nombre}.')
        return cleaned_data

class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre_completo', 'correo_electronico', 'mensaje']

class LoteProductoForm(forms.ModelForm):
    class Meta:
        model = LoteProducto
        fields = ['producto', 'cantidad', 'fecha_vencimiento']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }
        
class ArchivoVentasForm(forms.Form):
    archivo = forms.FileField(label="Archivo de ventas (.csv o .xlsx)")