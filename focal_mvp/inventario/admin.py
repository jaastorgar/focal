from django.contrib import admin
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
    DetalleOrden
)

# --- Clases Inline para una mejor visualización ---

class OfertaProductoInline(admin.TabularInline):
    """Permite ver y agregar las empresas que venden un producto y sus precios."""
    model = OfertaProducto
    fields = ('empresa', 'precio_compra', 'precio_venta')
    autocomplete_fields = ['empresa']
    extra = 1 

class LoteProductoInline(admin.TabularInline):
    """Permite ver y agregar lotes directamente desde la página de un producto."""
    model = LoteProducto
    readonly_fields = ('creado',)
    extra = 0

class SuscripcionUsuarioInline(admin.StackedInline):
    """Muestra la suscripción directamente en la página de la empresa."""
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
class AlmaceneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'correo', 'empresa')
    search_fields = ('nombre', 'apellido', 'run', 'correo', 'usuario__username')
    autocomplete_fields = ['usuario', 'empresa']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'marca', 'categoria', 'dramage')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'sku', 'marca')
    inlines = [OfertaProductoInline, LoteProductoInline]

@admin.register(LoteProducto)
class LoteProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad', 'fecha_vencimiento', 'creado')
    list_filter = ('fecha_vencimiento',)
    search_fields = ('producto__nombre', 'producto__sku')
    autocomplete_fields = ['producto']
    list_select_related = ('producto',)

# --- Registros de modelos restantes ---

admin.site.register(PlanSuscripcion)
admin.site.register(SuscripcionUsuario)
admin.site.register(OrdenVenta)
admin.site.register(DetalleOrden)
admin.site.register(MovimientoStock)