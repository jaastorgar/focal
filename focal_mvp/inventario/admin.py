from django.contrib import admin
# Se importa el UserAdmin para poder personalizar el admin de Almacenero
from django.contrib.auth.admin import UserAdmin
from .models import (
    PlanSuscripcion, 
    SuscripcionUsuario, 
    Empresa, 
    Almacenero, 
    Producto,
    OfertaProducto, 
    LoteProducto, 
    MovimientoStock, 
    OrdenVenta, 
    DetalleOrden,
    Proveedor
)

# --- Clases Inline (sin cambios) ---

class OfertaProductoInline(admin.TabularInline):
    model = OfertaProducto
    fields = ('empresa', 'precio_compra', 'precio_venta')
    autocomplete_fields = ['empresa']
    extra = 1 

class SuscripcionUsuarioInline(admin.StackedInline):
    model = SuscripcionUsuario
    extra = 0
    readonly_fields = ('fecha_inicio', 'fecha_fin')


# --- Configuraciones del Panel de Administrador ---

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre_almacen', 'rut', 'giro_negocio')
    search_fields = ('nombre_almacen', 'rut')
    inlines = [SuscripcionUsuarioInline]

@admin.register(Almacenero)
class AlmaceneroAdmin(UserAdmin):
    """
    Se personaliza el admin para el modelo de usuario Almacenero.
    Heredamos de UserAdmin para mantener toda la funcionalidad de Django.
    """
    # Usamos los campos correctos del modelo: nombre, apellido, email.
    list_display = ('email', 'nombres', 'apellidos', 'run', 'is_staff')
    search_fields = ('nombres', 'apellidos', 'run', 'email')
    ordering = ('email',)
    
    # Se ajustan los fieldsets para que el admin muestre los campos personalizados
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombres', 'apellidos', 'run', 'telefono', 'direccion', 'region', 'comuna', 'fecha_nacimiento', 'empresa')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombres', 'apellidos', 'run', 'password', 'password2'),
        }),
    )

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'marca', 'categoria', 'dramage')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'sku', 'marca')
    # Ya no se necesita el inline de Oferta aquí si se gestiona por separado
    # inlines = [OfertaProductoInline]

@admin.register(OfertaProducto)
class OfertaProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'empresa', 'precio_venta_base', 'activo') 
    
    search_fields = ('producto__nombre', 'empresa__nombre_almacen')
    list_filter = ('activo', 'empresa') 
    autocomplete_fields = ['producto', 'empresa']

@admin.register(LoteProducto)
class LoteProductoAdmin(admin.ModelAdmin):
    list_display = ('get_producto_nombre', 'get_empresa_nombre', 'cantidad', 'fecha_vencimiento', 'fecha_ingreso')
    list_filter = ('fecha_vencimiento', 'producto__empresa')
    search_fields = ('producto__producto__nombre', 'producto__producto__sku')
    autocomplete_fields = ['producto']

    def get_producto_nombre(self, obj):
        return obj.producto.producto.nombre
    get_producto_nombre.short_description = 'Producto'

    def get_empresa_nombre(self, obj):
        return obj.producto.empresa.nombre_almacen
    get_empresa_nombre.short_description = 'Empresa'

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'contacto', 'telefono', 'email')
    search_fields = ('nombre', 'rut', 'contacto')
    list_filter = ('region',)

# --- Registros de Modelos Adicionales (sin cambios) ---
admin.site.register(PlanSuscripcion)
admin.site.register(MovimientoStock)
admin.site.register(OrdenVenta)
admin.site.register(DetalleOrden)
admin.site.register(SuscripcionUsuario)