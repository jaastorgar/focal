from django.contrib import admin
from .models import Producto, Almacenero, PlanSuscripcion, SuscripcionUsuario, Empresa

# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'stock', 'precio_unitario')
    search_fields = ('nombre', 'codigo')

@admin.register(Almacenero)
class AlmaceneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'run', 'usuario', 'comuna')
    search_fields = ('nombre', 'run', 'usuario__username')

@admin.register(PlanSuscripcion)
class PlanSuscripcionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'max_productos', 'max_almacenes', 'soporte_prioritario')
    search_fields = ('nombre',)
    
@admin.register(SuscripcionUsuario)
class SuscripcionUsuarioAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'plan', 'fecha_inicio', 'fecha_fin', 'activa')
    search_fields = ('empresa__nombre_almacen', 'plan__nombre')

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre_almacen', 'rut', 'direccion_tributaria', 'comuna', 'run_representante', 'inicio_actividades', 'nivel_venta_uf', 'giro_negocio', 'tipo_sociedad')
    search_fields = ('nombre_almacen', 'rut', 'run_representante')
    list_filter = ('tipo_sociedad',)