from django.urls import path
from .views import vista_registro, vista_login

urlpatterns = [
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
]