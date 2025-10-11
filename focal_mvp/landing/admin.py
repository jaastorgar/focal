from django.contrib import admin
from .models import Contacto

# Register your models here.
@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'email', 'fecha_envio')
    search_fields = ('nombre_completo', 'email')
    list_filter = ('fecha_envio',)
