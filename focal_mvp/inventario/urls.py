from django.urls import path
from .views import vista_registro, vista_login, home, vista_planes, seleccionar_plan, logout_view, perfil, inventario_view, agregar_producto, editar_producto, eliminar_producto, agregar_lote_producto, detalle_producto, editar_lote, eliminar_lote, retirar_lote, historial_movimientos_view, inventario_dashboard_data

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
    path('productos/eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('lotes/agregar/', agregar_lote_producto, name='agregar_lote'),
    path('productos/<int:producto_id>/lotes/', detalle_producto, name='detalle_producto'),
    path('lotes/<int:lote_id>/editar/', editar_lote, name='editar_lote'),
    path('lotes/<int:lote_id>/eliminar/', eliminar_lote, name='eliminar_lote'),
    path('lotes/<int:lote_id>/retirar/', retirar_lote, name='retirar_lote'),
    path('historial-movimientos/', historial_movimientos_view, name='historial_movimientos'),
    path('api/dashboard-data/', inventario_dashboard_data, name='inventario_dashboard_data'),
]