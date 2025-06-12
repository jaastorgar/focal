from django.urls import path
from .views import procesar_ventas_archivo, dashboard_metrics_api

urlpatterns = [
    path('ventas/archivo/', procesar_ventas_archivo, name='procesar_ventas_archivo'),
    path('dashboard-metrics/', dashboard_metrics_api, name='dashboard-metrics'),
]