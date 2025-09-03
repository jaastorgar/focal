from django.urls import path
from .views import ( 
landing_page_view, contacto_submit_view, vista_login, vista_registro, 
vista_planes, get_comunas, quienes_somos_view
)

urlpatterns = [
    path('', landing_page_view, name='landing'),
    path('contacto/enviar/', contacto_submit_view, name='contacto_submit'),
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
    path('planes/', vista_planes, name='planes'),
    path('get-comunas/', get_comunas, name='get_comunas'),
    path('quienes_somos/', quienes_somos_view, name='quienes_somos')
]