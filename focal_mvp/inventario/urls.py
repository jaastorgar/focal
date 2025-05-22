from django.urls import path
from .views import vista_registro, vista_login, home, vista_planes, seleccionar_plan, logout_view, perfil, inventario_view, agregar_producto, editar_producto

urlpatterns = [
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
    path('home/', home, name='home'),
    path('planes/', vista_planes, name='planes'),
    path('seleccionar-plan/<int:plan_id>/', seleccionar_plan, name='seleccionar_plan'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil, name='perfil'),
    path('inventario/', inventario_view, name='inventario'),
    path('agregar-producto/', agregar_producto, name='agregar-producto'),
    path('editar-producto/<int:producto_id>/', editar_producto, name='editar-producto'),
]