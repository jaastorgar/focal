from django.urls import path
from .views import procesar_ventas_archivo

urlpatterns = [
    path('ventas/archivo/', procesar_ventas_archivo, name='procesar_ventas_archivo'),
]