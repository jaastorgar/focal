from django.urls import path
from .views import landing_page_view, contacto_submit_view, vista_login, vista_registro, vista_planes

urlpatterns = [
    path('', landing_page_view, name='landing'),
    path('contacto/enviar/', contacto_submit_view, name='contacto_submit'),
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
    path('planes/', vista_planes, name='planes'),
]