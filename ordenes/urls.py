from django.urls import path
from .views import *


urlpatterns = [
    path('crearOrden/', crearOrden.as_view(), name='crear_orden'),
    path('obtenerListaPedidosPendientes/', obtenerListaPedidosPendientes.as_view(), name='obtener_lista_pedidos_pendientes'),
    path('obtenerMesasConPedidosAbiertos/', ObtenerMesasConPedidosAbiertos.as_view(), name='obtener_pedidos_por_mesa'),
    path('actualizarStatusorden/<int:id>/', actualizarStatusorden.as_view(), name='actualizar_status_orden'),
    path('ObtenerTodosPedidosOrdenes/', obtenerTodosPedidosOrdenes.as_view(), name='obtener_todos_pedidos_ordenes'),
    path('TotalVentasPorFecha/', TotalVentasPorFecha.as_view(), name='TotalVentasPorFecha'),
]
