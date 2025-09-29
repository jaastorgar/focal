from django.urls import path
from .views import finanza_view

urlpatterns = [
    path('finanza', finanza_view, name='finanzas')
]
