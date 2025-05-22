from django.urls import path
from .views import vista_registro, vista_login, home, vista_planes, seleccionar_plan

urlpatterns = [
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
    path('home/', home, name='home'),
    path('planes/', vista_planes, name='planes'),
    path('seleccionar-plan/<int:plan_id>/', seleccionar_plan, name='seleccionar_plan'),
]