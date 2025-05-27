from django import forms
from django.contrib.auth.models import User
from .models import Empresa, Producto
from django.forms.widgets import DateInput

# Clase para aplicar 'form-control' a los widgets
class BootstrapFormMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif 'class' not in field.widget.attrs:
                 field.widget.attrs.update({'class': 'form-control'})

class AlmaceneroForm(BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(label="Nombre de usuario",
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: usuario.focal'}))
    password = forms.CharField(label="Contraseña",
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'}))
    confirm_password = forms.CharField(label="Confirmar contraseña",
                                       widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita su contraseña'}))

    nombre = forms.CharField(label="Primer nombre", widget=forms.TextInput(attrs={'class': 'form-control'}))
    snombre = forms.CharField(label="Segundo nombre", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(label="Apellido paterno", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sapellido = forms.CharField(label="Apellido materno", widget=forms.TextInput(attrs={'class': 'form-control'}))
    run = forms.CharField(label="RUN (sin puntos ni guion)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 123456789'}))
    telefono = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +56912345678'}))
    direccion = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    comuna = forms.CharField(label="Comuna", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    fecha_nacimiento = forms.DateField(label="Fecha de nacimiento", required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

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

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'sku',
            'marca',
            'categoria',
            'unidad_medida',
            'stock',
            'precio_compra',
            'precio_venta',
            'fecha_vencimiento',
        ]
        widgets = {
            'fecha_vencimiento': DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'sku': 'Sku (Código Único)',
            'marca': 'Marca',
            'categoria': 'Categoría',
            'unidad_medida': 'Unidad de Medida',
            'stock': 'Stock Disponible',
            'precio_compra': 'Precio de Compra',
            'precio_venta': 'Precio de Venta',
            'fecha_vencimiento': 'Fecha de Vencimiento',
        }
    
    # Validación personalizada opcional (por ejemplo, stock o precio negativos)
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock

    def clean_precio_venta(self):
        precio = self.cleaned_data.get('precio_venta')
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio
    
class RetirarStockForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all().order_by('nombre'),
        label="Seleccionar Producto",
        empty_label="--- Seleccione un producto ---",
        widget=forms.Select(attrs={'class': 'form-control'}) # Añade una clase para estilos si usas CSS
    )
    
    cantidad = forms.IntegerField(
        label="Cantidad a Retirar",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}) # Añade una clase para estilos
    )

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if producto and cantidad:
            if cantidad > producto.stock:
                self.add_error('cantidad', f'No hay suficiente stock. Solo quedan {producto.stock} unidades de {producto.nombre}.')
        return cleaned_data