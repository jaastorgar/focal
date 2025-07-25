import re
from django import forms
from django.contrib.auth.models import User
from .models import Empresa, Producto, LoteProducto, Almacenero, OfertaProducto
from django.forms import modelformset_factory # Necesario para el formset
from django.forms.widgets import DateInput, TextInput, Textarea, Select, EmailInput, NumberInput, PasswordInput, CheckboxInput

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

    class Meta:
        model = Almacenero
        fields = ['nombre', 'snombre', 'apellido', 'sapellido', 'run', 'correo', 'telefono', 'direccion', 'comuna', 'fecha_nacimiento']
        widgets = {'fecha_nacimiento': DateInput(attrs={'type': 'date'})}
        labels = {'nombre': "Primer nombre", 'snombre': "Segundo nombre", 'apellido': "Apellido paterno", 'sapellido': "Apellido materno", 'run': "RUN (sin puntos ni guion)", 'correo': "Correo electrónico", 'telefono': "Teléfono", 'direccion': "Dirección", 'comuna': "Comuna", 'fecha_nacimiento': "Fecha de nacimiento"}

    def clean_run(self):
        run = self.cleaned_data['run']
        run_limpio = re.sub(r'[\.-]', '', run).upper().strip()
        if not validar_run_rut(run_limpio):
            raise forms.ValidationError("El RUN es inválido.")
        if Almacenero.objects.filter(run=run_limpio).exists():
            raise forms.ValidationError("Ya existe un Almacenero con este RUN.")
        return run_limpio
    
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if not correo:
            raise forms.ValidationError("El correo electrónico es requerido.")
        if Almacenero.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Ya existe un Almacenero con este correo electrónico.")
        return correo

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")
        elif p1 and not validar_password_segura(p1):
            self.add_error("password", "La contraseña debe tener entre 8 y 12 caracteres, incluyendo al menos una mayúscula, una minúscula, un número y un símbolo.")
        return cleaned_data

class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre_almacen', 'rut', 'direccion_tributaria', 'comuna', 'run_representante', 'inicio_actividades', 'nivel_venta_uf', 'giro_negocio', 'tipo_sociedad']
        widgets = {'inicio_actividades': DateInput(attrs={'type': 'date'})}
        labels = {'nombre_almacen': "Nombre del Almacén/Empresa", 'rut': "RUT de la Empresa", 'direccion_tributaria': "Dirección Tributaria", 'comuna': "Comuna de la Empresa", 'run_representante': "RUN del Representante Legal", 'inicio_actividades': "Fecha de Inicio de Actividades", 'nivel_venta_uf': "Nivel de Ventas (UF)", 'giro_negocio': "Giro de Negocio", 'tipo_sociedad': "Tipo de Sociedad"}

    def clean_run_representante(self):
        run = self.cleaned_data['run_representante']
        run_limpio = re.sub(r'[\.-]', '', run).upper().strip()
        if not validar_run_rut(run_limpio):
            raise forms.ValidationError("El RUN del representante es inválido.")
        return run_limpio

    def clean_rut(self): 
        rut = self.cleaned_data['rut']
        rut_limpio = re.sub(r'[\.-]', '', rut).upper().strip()
        if not validar_run_rut(rut_limpio):
            raise forms.ValidationError("El RUT de la empresa es inválido.")
        if Empresa.objects.filter(rut=rut_limpio).exists():
            raise forms.ValidationError("Ya existe una Empresa con este RUT.")
        return rut_limpio

class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario simplificado para los datos intrínsecos del producto.
    Los precios y la empresa se manejan ahora en el formset de ofertas.
    """
    class Meta:
        model = Producto
        fields = ['sku', 'nombre', 'marca', 'categoria', 'dramage', 'unidad_medida']
        widgets = {
            'sku': forms.TextInput(attrs={'placeholder': 'Ej: 0123456789123'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Leche Entera 1L'}),
            'marca': forms.TextInput(attrs={'placeholder': 'Ej: Soprole'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'dramage': forms.NumberInput(attrs={'placeholder': 'Cantidad del producto'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'sku': 'SKU (Código Único)',
            'nombre': 'Nombre del Producto',
            'marca': 'Marca',
            'categoria': 'Categoría',
            'dramage': 'Cantidad (ej: 150 para 150gr)',
            'unidad_medida': 'Unidad de Medida',
        }

class OfertaProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OfertaProducto
        fields = ['precio_compra', 'precio_venta']

    def clean(self):
        cleaned_data = super().clean()
        precio_venta = cleaned_data.get('precio_venta')
        precio_compra = cleaned_data.get('precio_compra')

        if precio_venta is not None and precio_compra is not None:
            if precio_venta <= precio_compra:
                raise forms.ValidationError(
                    "El precio de venta debe ser mayor que el de compra para asegurar un margen."
                )
        return cleaned_data

# 2. Modifica OfertaProductoFormSet
OfertaProductoFormSet = modelformset_factory(
    OfertaProducto,
    form=OfertaProductoForm,
    fields=('precio_compra', 'precio_venta'),
    extra=1,
    can_delete=True
)

class RetirarStockForm(forms.Form): 
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(), 
        label="Seleccionar Producto",
        widget=Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.IntegerField(
        label="Cantidad a Retirar",
        min_value=1,
        widget=NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated and hasattr(user, 'almacenero') and user.almacenero.empresa:
            empresa_del_usuario = user.almacenero.empresa
            self.fields['producto'].queryset = Producto.objects.filter(empresas=empresa_del_usuario).order_by('nombre')
        else:
            self.fields['producto'].queryset = Producto.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if producto and cantidad:
            stock_total_producto = sum(lote.cantidad for lote in producto.lotes.all()) 
            if cantidad > stock_total_producto:
                self.add_error('cantidad', f'No hay suficiente stock. Solo quedan {stock_total_producto} unidades de {producto.nombre}.')
        return cleaned_data

# --- Formularios restantes (sin cambios) ---

class LoteProductoForm(forms.ModelForm):
    class Meta:
        model = LoteProducto
        fields = ['cantidad', 'fecha_vencimiento'] 
        widgets = {'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'})}

class ArchivoVentasForm(forms.Form):
    archivo_ventas = forms.FileField(
        label='Archivo de ventas (.csv o .xlsx)',
        widget=forms.ClearableFileInput(attrs={'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'})
    )