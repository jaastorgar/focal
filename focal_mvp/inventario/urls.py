from django.urls import path
from .views import (
    home, seleccionar_plan, logout_view, perfil, inventario_view,
    agregar_producto, editar_producto, eliminar_producto,
    agregar_lote_producto, detalle_producto, editar_lote, eliminar_lote,
    retirar_lote, descargar_plantilla_ventas, procesar_ventas_archivo,
    buscar_producto_api, verificar_producto_api, obtener_datos_sku_api,
    gestionar_proveedores_precios
)

urlpatterns = [
    path('home/', home, name='home'),
    path('planes/seleccionar/<int:plan_id>/', seleccionar_plan, name='seleccionar_plan'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil, name='perfil'),
    path('inventario/', inventario_view, name='inventario'),
    path('productos/agregar/', agregar_producto, name='agregar-producto'),
    path('productos/editar/<int:producto_id>/', editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),
    path('lotes/agregar/', agregar_lote_producto, name='agregar_lote'),
    path('productos/<int:producto_id>/lotes/', detalle_producto, name='detalle_producto'),
    path('lotes/<int:lote_id>/editar/', editar_lote, name='editar_lote'),
    path('lotes/<int:lote_id>/eliminar/', eliminar_lote, name='eliminar_lote'),
    path('lotes/<int:lote_id>/retirar/', retirar_lote, name='retirar_lote'),
    path('descargar-plantilla/', descargar_plantilla_ventas, name='descargar_plantilla'),
    path('procesar-ventas-archivo/', procesar_ventas_archivo, name='procesar_ventas_archivo'),
    path('api/buscar-producto/<str:codigo_barras>/', buscar_producto_api, name='buscar_producto_api'),
    path('api/verificar-producto/<str:codigo_barras>/', verificar_producto_api, name='verificar_producto_api'),
    path('api/obtener-datos-sku/<str:sku>/', obtener_datos_sku_api, name='obtener_datos_sku_api'),
    path('inventario/<int:producto_id>/proveedores-precios/', gestionar_proveedores_precios, name='gestionar_proveedores_precios'),
]