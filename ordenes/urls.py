from django.urls import path
from .views import *


urlpatterns = [
    path('crearOrden/', crearOrden.as_view(), name='crear_orden'),
    path('obtenerListaPedidosPendientes/', obtenerListaPedidosPendientes.as_view(), name='obtener_lista_pedidos_pendientes'),
    path('obtenerMesasConPedidosAbiertos/', ObtenerTodasLasMesasConProductos.as_view(), name='obtener_pedidos_por_mesa'),
    path('actualizarStatusorden/<int:detalle_id>/', ActualizarStatusDetalle.as_view(), name='actualizar_status_orden'),
    path('CompletarYTotalPedido/<int:pedido_id>/', CompletarYTotalPedido.as_view(), name='completar_y_total_pedido'),
    path('ObtenerTodosPedidosOrdenes/', obtenerTodosPedidosOrdenes.as_view(), name='obtener_todos_pedidos_ordenes'),
    path('TotalVentasPorFecha/', TotalVentasPorRangoFechas.as_view(), name='TotalVentasPorFecha'),
]
