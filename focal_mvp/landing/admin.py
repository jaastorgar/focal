from django.contrib import admin
from .models import Contacto

# Register your models here.
@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'correo_electronico', 'fecha_envio')
    search_fields = ('nombre_completo', 'correo_electronico')
    list_filter = ('fecha_envio',)
