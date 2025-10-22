from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import (
    Producto,
    LoteProducto,
    OfertaProducto,
    Almacenero,
    Empresa,
    Proveedor,
    Recordatorio,
    REGIONES_COMUNAS,
)
import re

# --- TUS FUNCIONES DE VALIDACIÓN ---
def validar_run_rut(run_rut):
    run_rut = str(run_rut).upper().strip()
    run_rut = re.sub(r'[.-]', '', run_rut)
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
    class Meta:
        model = Producto
        exclude = ('empresas',)

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa_usuario', None)
        super().__init__(*args, **kwargs)

        # Clases base
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

        # Endurecer input del SKU en el DOM
        if 'sku' in self.fields:
            self.fields['sku'].widget.attrs.update({
                'maxlength': '30',
                'inputmode': 'numeric',   # teclado numérico en móviles
                'pattern': r'[0-9]*',     # ayuda al browser, no reemplaza el backend
                'autocomplete': 'off',
                'placeholder': 'Solo números (máx. 30)'
            })

    def clean_sku(self):
        sku = (self.cleaned_data.get('sku') or '').strip()

        # 1) Sin espacios en ninguna parte
        if re.search(r'\s', sku):
            raise forms.ValidationError("El SKU no debe contener espacios.")

        # 2) Solo dígitos
        if not sku.isdigit():
            raise forms.ValidationError("El SKU debe contener solo números.")

        # 3) Máximo 30 dígitos (sin mínimo)
        if len(sku) > 30:
            raise forms.ValidationError("El SKU no puede superar los 30 dígitos.")

        # 4) Duplicidad en el inventario de la empresa (mantengo tu lógica)
        if sku and self.empresa:
            qs = OfertaProducto.objects.filter(producto__sku=sku, empresa=self.empresa)
            if self.instance and self.instance.pk:
                qs = qs.exclude(producto=self.instance)
            if qs.exists():
                raise forms.ValidationError("Este SKU ya está siendo utilizado por otro producto en tu inventario.")

        return sku

class OfertaProductoForm(forms.ModelForm):
    class Meta:
        model = OfertaProducto
        exclude = ('empresa',)

    def __init__(self, empresa=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        if producto:
            if OfertaProducto.objects.filter(producto=producto, empresa=self.empresa).exists():
                raise forms.ValidationError("Ya existe una oferta para este producto en tu inventario.")
        return cleaned_data

class LoteProductoForm(forms.ModelForm):
    class Meta:
        model = LoteProducto
        exclude = ['fecha_ingreso']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'numero_factura': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Número de factura (opcional)'
            }),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # <-- importante para filtrar opciones por empresa
        self.empresa_usuario = kwargs.pop('empresa_usuario', None)
        super().__init__(*args, **kwargs)

        # Asegura clases CSS en todos los campos de texto/numéricos
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

        # ===== MODO EDICIÓN =====
        # Si estamos editando un lote existente, NO pedimos 'producto'
        if self.instance and self.instance.pk:
            # Quitamos el campo para que no lo valide ni lo pida en el POST
            self.fields.pop('producto', None)
        else:
            # ===== MODO CREACIÓN =====
            # Filtramos 'producto' (Ofertas) por la empresa actual
            if 'producto' in self.fields:
                if self.empresa_usuario:
                    self.fields['producto'].queryset = OfertaProducto.objects.filter(
                        empresa=self.empresa_usuario
                    ).select_related('producto')
                else:
                    self.fields['producto'].queryset = OfertaProducto.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio_compra = cleaned_data.get('precio_compra')
        precio_venta = cleaned_data.get('precio_venta')

        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        if precio_compra is None or precio_compra < 0:
            raise forms.ValidationError("El precio de compra no puede ser negativo.")
        if precio_venta is None or precio_venta < 0:
            raise forms.ValidationError("El precio de venta no puede ser negativo.")
        return cleaned_data

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        # Dejamos únicamente los campos que quieres usar en el formulario
        fields = ['nombre', 'razon_social', 'rut', 'contacto', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre comercial'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón social'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '76.123.456-K'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'proveedor@correo.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegura clases en caso de que cambien widgets a futuro
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if 'form-control' not in css:
                field.widget.attrs['class'] = (css + ' form-control').strip()

class RecordatorioForm(forms.ModelForm):
    class Meta:
        model = Recordatorio
        fields = [
            'nombre', 'descripcion', 'tipo_obligacion', 'periodicidad',
            'dia_mes', 'mes_anio', 'fecha_primera_ejecucion',
            'proxima_fecha_ejecucion', 'dias_anticipacion_alerta', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la obligación'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada'}),
            'tipo_obligacion': forms.Select(attrs={'class': 'form-select'}),
            'periodicidad': forms.Select(attrs={'class': 'form-select'}),
            'dia_mes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Día (1-31)', 'min': 1, 'max': 31}),
            'mes_anio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mes (1-12)', 'min': 1, 'max': 12}),
            'fecha_primera_ejecucion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proxima_fecha_ejecucion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dias_anticipacion_alerta': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30, 'placeholder': '5'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.SelectMultiple, forms.CheckboxInput)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_obligacion = cleaned_data.get('tipo_obligacion')
        periodicidad = cleaned_data.get('periodicidad')
        dia_mes = cleaned_data.get('dia_mes')
        mes_anio = cleaned_data.get('mes_anio')
        fecha_primera_ejecucion = cleaned_data.get('fecha_primera_ejecucion')
        proxima_fecha_ejecucion = cleaned_data.get('proxima_fecha_ejecucion')
        
        if tipo_obligacion in ['fija', 'variable'] and not periodicidad:
            raise forms.ValidationError("Debe seleccionar una periodicidad para obligaciones fijas o variables.")
        
        if tipo_obligacion == 'fija':
            if dia_mes and (dia_mes < 1 or dia_mes > 31):
                raise forms.ValidationError("El día del mes debe estar entre 1 y 31.")
            if mes_anio and (mes_anio < 1 or mes_anio > 12):
                raise forms.ValidationError("El mes del año debe estar entre 1 y 12.")
        
        if not fecha_primera_ejecucion:
            raise forms.ValidationError("Debe ingresar la fecha de primera ejecución.")
        
        if not proxima_fecha_ejecucion:
            raise forms.ValidationError("Debe ingresar la próxima fecha de ejecución.")
        
        if proxima_fecha_ejecucion < fecha_primera_ejecucion:
            raise forms.ValidationError("La próxima fecha de ejecución no puede ser anterior a la fecha de primera ejecución.")
        
        return cleaned_data    