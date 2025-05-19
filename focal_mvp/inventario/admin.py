from django.contrib import admin
from .models import Producto, Almacenero

# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'stock', 'precio_unitario')
    search_fields = ('nombre', 'codigo')

@admin.register(Almacenero)
class AlmaceneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'usuario', 'comuna')
    search_fields = ('nombre', 'rut', 'usuario__username')