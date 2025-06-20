from django.urls import path
from .views import landing_page, contacto_view

urlpatterns = [
    path('', landing_page, name='landing'),
    path('contacto/', contacto_view, name='contacto'),
]