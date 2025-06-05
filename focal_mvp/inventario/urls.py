from django.urls import path
from .views import vista_registro, vista_login, home, vista_planes, seleccionar_plan, logout_view, perfil, inventario_view, agregar_producto, editar_producto, retirar_stock_view, eliminar_producto, agregar_lote_producto, detalle_producto

urlpatterns = [
    path('registro/', vista_registro, name='registro'),
    path('login/', vista_login, name='login'),
    path('home/', home, name='home'),
    path('planes/', vista_planes, name='planes'),
    path('seleccionar-plan/<int:plan_id>/', seleccionar_plan, name='seleccionar_plan'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil, name='perfil'),
    path('inventario/', inventario_view, name='inventario'),
    path('productos/agregar/', agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:producto_id>/', editar_producto, name='editar_producto'),
    path('retirar-stock/', retirar_stock_view, name='retirar_stock'),
    path('productos/eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('lotes/agregar/', agregar_lote_producto, name='agregar_lote'),
    path('productos/<int:producto_id>/lotes/', detalle_producto, name='detalle_producto'),
]