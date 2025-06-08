from django.urls import path
from .views import DescontarStockView

urlpatterns = [
    path('descontar-stock/', DescontarStockView.as_view(), name='descontar_stock_api'),
]