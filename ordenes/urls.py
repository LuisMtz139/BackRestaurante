from django.urls import path
from .views import *


urlpatterns = [
	path('crearOrden/', crearOrden.as_view(), name='crear_orden'),
	path('obtenerListaPedidosPendientes/', obtenerListaPedidosPendientes.as_view(), name='obtener_lista_pedidos_pendientes'),
	path('obtenerMesasConPedidosAbiertos/', ObtenerTodasLasMesasConProductos.as_view(), name='obtener_pedidos_por_mesa'),
	path('actualizarStatusorden/<int:detalle_id>/', ActualizarStatusDetalle.as_view(), name='actualizar_status_orden'),
	path('agregarProductosAPedido/', agregarProductosAPedido.as_view(), name='agregar_productos_a_pedido'),
	path('CompletarYTotalPedido/<int:pedido_id>/', CompletarYTotalPedido.as_view(), name='completar_y_total_pedido'),
	path('ObtenerTodosPedidosOrdenes/', obtenerTodosPedidosOrdenes.as_view(), name='obtener_todos_pedidos_ordenes'),
	path('TotalVentasPorFecha/', TotalVentasPorRangoFechas.as_view(), name='TotalVentasPorFecha'),
	path('detalle/<int:detalleId>/actualizarCantidad/', ActualizarCantidadDetalle.as_view(), name='actualizar_cantidad_detalle'),
	path('pedido/<int:pedidoId>/detalles/eliminar/', EliminarDetallesDePedido.as_view(), name='eliminar_detalles_pedido'),
	path('<int:idMesa>/eliminarPedido/', EliminarPedidoCompleto.as_view(), name='eliminar_pedido_completo'),
	path('ObtenerHistorialVentasPorDia/', ObtenerHistorialVentasPorDia.as_view(), name='obtener_historial_ventas_por_dia')

]
