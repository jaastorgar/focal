import re
from django import forms
from django.contrib.auth.models import User
# Asegúrate de importar Almacenero además de Empresa, Producto, LoteProducto
from .models import Empresa, Producto, LoteProducto, Almacenero # <-- Asegúrate que Almacenero esté aquí
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
    # Estos campos son para el modelo User, no para Almacenero,
    # por eso los definimos explícitamente y se manejan en la vista.
    username = forms.CharField(label="Nombre de usuario", widget=forms.TextInput(attrs={'placeholder': 'Ej: focal'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}))
    confirm_password = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={'placeholder': 'Repita su contraseña'}))

    class Meta:
        model = Almacenero
        fields = [
            'nombre', 'snombre', 'apellido', 'sapellido', 'run', 'correo',
            'telefono', 'direccion', 'comuna', 'fecha_nacimiento'
        ]
        widgets = {
            'fecha_nacimiento': DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'nombre': "Primer nombre",
            'snombre': "Segundo nombre",
            'apellido': "Apellido paterno",
            'sapellido': "Apellido materno",
            'run': "RUN (sin puntos ni guion)",
            'correo': "Correo electrónico",
            'telefono': "Teléfono",
            'direccion': "Dirección",
            'comuna': "Comuna",
            'fecha_nacimiento': "Fecha de nacimiento",
        }

    def clean_run(self):
        run = self.cleaned_data['run']
        run_limpio = re.sub(r'[\.-]', '', run).upper().strip()
        if not validar_run_rut(run_limpio):
            raise forms.ValidationError("El RUN es inválido.")
        if Almacenero.objects.filter(run=run_limpio).exists():
            raise forms.ValidationError("Ya existe un Almacenero con este RUN.")
        return run_limpio
    
    # CAMBIO AQUÍ: Validación para asegurar que el correo no esté vacío y sea único
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        
        # Primero, verifica si el campo está vacío
        if not correo:
            raise forms.ValidationError("El correo electrónico es requerido.")

        # Luego, verifica la unicidad
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

    # CAMBIO: Renombrado de clean_rut_empresa a clean_rut para que Django lo asocie automáticamente al campo 'rut'
    def clean_rut(self): 
        rut = self.cleaned_data['rut'] # CAMBIO: Acceder a 'rut' no a 'rut_empresa'
        rut_limpio = re.sub(r'[\.-]', '', rut).upper().strip()

        if not validar_run_rut(rut_limpio):
            raise forms.ValidationError("El RUT de la empresa es inválido. Por favor, verifique el formato y el dígito verificador.")
        
        # Opcional: Asegurarse de que el RUT no exista ya para una Empresa
        if Empresa.objects.filter(rut=rut_limpio).exists():
            raise forms.ValidationError("Ya existe una Empresa con este RUT.")

        return rut_limpio

class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'sku',
            'marca',
            'categoria',
            'dramage',
            'unidad_medida',
            'precio_compra',
            'precio_venta',
        ]
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'gramage': forms.NumberInput(attrs={'placeholder': 'Cantidad del producto'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Leche Entera 1L'}),
            'sku': forms.TextInput(attrs={'placeholder': 'Ej: LECH-ENT-1L-SOP'}),
            'marca': forms.TextInput(attrs={'placeholder': 'Ej: Soprole'}),
            'precio_compra': forms.NumberInput(attrs={'placeholder': 'Costo del producto'}),
            'precio_venta': forms.NumberInput(attrs={'placeholder': 'Precio al público'}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'sku': 'SKU (Código Único)',
            'marca': 'Marca',
            'categoria': 'Categoría',
            'dramage': 'Cantidad de dramage',
            'unidad_medida': 'Unidad de Medida',
            'precio_compra': 'Precio de Compra',
            'precio_venta': 'Precio de Venta',
        }

    def clean_precio_venta(self):
        """
        Asegura que el precio de venta sea mayor que el precio de compra.
        """
        precio_venta = self.cleaned_data.get('precio_venta')
        precio_compra = self.cleaned_data.get('precio_compra')

        # Es importante verificar que ambos valores existan antes de compararlos
        if precio_venta is not None and precio_compra is not None:
            if precio_venta <= precio_compra:
                raise forms.ValidationError(
                    "El precio de venta debe ser mayor que el precio de compra para asegurar un margen."
                )
        
        return precio_venta
    
class RetirarStockForm(forms.Form): 
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(), 
        label="Seleccionar Producto",
        empty_label="--- Seleccione un producto ---",
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
            self.fields['producto'].queryset = Producto.objects.filter(empresa=user.almacenero.empresa).order_by('nombre')
        else:
            pass

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if producto and cantidad:
            stock_total_producto = sum(lote.cantidad for lote in producto.lotes.all()) 
            if cantidad > stock_total_producto:
                self.add_error('cantidad', f'No hay suficiente stock. Solo quedan {stock_total_producto} unidades de {producto.nombre}.')
        return cleaned_data

class LoteProductoForm(forms.ModelForm):
    class Meta:
        model = LoteProducto
        fields = ['producto', 'cantidad', 'fecha_vencimiento'] 
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Constructor personalizado para aceptar el argumento 'empresa' y filtrar
        el queryset del campo 'producto'.
        """
        # 1. Extraemos el argumento 'empresa' que le pasamos desde la vista.
        empresa = kwargs.pop('empresa', None)
        
        # 2. Llamamos al constructor original del formulario.
        super(LoteProductoForm, self).__init__(*args, **kwargs)

        # 3. Si se proporcionó una empresa, filtramos la lista de productos.
        if empresa:
            self.fields['producto'].queryset = Producto.objects.filter(empresa=empresa)
        
class ArchivoVentasForm(forms.Form):
    """
    Un formulario simple con un solo campo para subir el archivo de ventas.
    """
    archivo_ventas = forms.FileField(
        label='Archivo de ventas (.csv o .xlsx)',
        widget=forms.ClearableFileInput(attrs={'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'})
    )