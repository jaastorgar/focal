from django.urls import path
from .views import DescontarStockView, dashboard_metrics_api

urlpatterns = [
    path('descontar-stock/', DescontarStockView.as_view(), name='descontar_stock_api'),
    path('dashboard-metrics/', dashboard_metrics_api, name='dashboard-metrics'),
]