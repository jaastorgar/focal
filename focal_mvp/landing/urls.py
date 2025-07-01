from django.urls import path
from .views import landing_page_view, contacto_submit_view

urlpatterns = [
    path('', landing_page_view, name='landing'),
    path('contacto/enviar/', contacto_submit_view, name='contacto_submit'),
]