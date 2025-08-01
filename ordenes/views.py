
from rest_framework.views import APIView
from rest_framework.response import Response
from ordenes.models import *
from datetime import datetime
from ordenes.models import Pedido

class crearOrden(APIView):
    def post(self, request):
        nombreOrden = request.data.get("nombreOrden")
        mesaId = request.data.get("mesaId")
        productos = request.data.get("productos")
        status = request.data.get("status", "proceso")

        if not nombreOrden or not mesaId or not productos or not status:
            return Response({"error": "Todos los campos son obligatorios"}, status=400)

        pedido = Pedido.objects.create(
            nombreOrden=nombreOrden,
            idMesa_id=mesaId,
        )
        if not pedido:
            return Response({"error": "Error al crear el pedido"}, status=500)

        for producto in productos:
            productoId = producto.get("productoId")
            cantidad = producto.get("cantidad", 1)
            observaciones = producto.get("observaciones", "")
            if not productoId:
                continue
            # Verifica que el producto exista
            if not productoMenu.objects.filter(id=productoId).exists():
                return Response({"error": f"El producto con ID {productoId} no existe"}, status=400)
            DetallePedido.objects.create(
                pedido=pedido,
                producto_id=productoId,
                cantidad=cantidad,
                observaciones=observaciones,
                status=status  # Ahora el status es por detalle
            )

        return Response({
            "success": True,
            "pedidoId": pedido.id,
            "nombreOrden": pedido.nombreOrden,
            "mesaId": pedido.idMesa_id,
            "productos": productos
        }, status=201)
        
class obtenerListaPedidosPendientes(APIView):
    def get(self, request):
        pedidos = Pedido.objects.all().order_by('fecha')  # Trae todos los pedidos, puedes filtrar por mesa si necesitas
        pedidosPorMesa = []
        for pedido in pedidos:
            mesa = pedido.idMesa
            detalles = pedido.detalles.filter(status="proceso")  # Solo detalles pendientes
            listaDetalles = []
            for detalle in detalles:
                listaDetalles.append({
                    "productoId": detalle.producto.id if detalle.producto else None,
                    "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                    "cantidad": detalle.cantidad,
                    "observaciones": detalle.observaciones,
                    "status": detalle.status,
                })
            if not listaDetalles:
                continue  # Si no hay detalles pendientes, no mostrar el pedido

            pedidoInfo = {
                "pedidoId": pedido.id,
                "nombreOrden": pedido.nombreOrden,
                "fecha": pedido.fecha,
                "detalles": listaDetalles
            }
            mesaExistente = next((m for m in pedidosPorMesa if m["numeroMesa"] == mesa.numeroMesa), None)
            if not mesaExistente:
                pedidosPorMesa.append({
                    "numeroMesa": mesa.numeroMesa,
                    "pedidos": [pedidoInfo]
                })
            else:
                mesaExistente["pedidos"].append(pedidoInfo)
        
        if not pedidosPorMesa:
            return Response({"message": "No hay pedidos pendientes"}, status=200)

        return Response({
            "success": True,
            "pedidosPorMesa": pedidosPorMesa
        }, status=200)
        
class ObtenerTodasLasMesasConProductos(APIView):
    def get(self, request):
        mesas = Mesa.objects.all()  # Muestra todas las mesas, no solo abiertas
        if not mesas:
            return Response({"message": "No hay mesas registradas"}, status=200)

        mesasData = []
        for mesa in mesas:
            # Trae todos los pedidos de esa mesa
            pedidosMesa = mesa.pedido_set.all().order_by('fecha')
            productosData = []
            for pedido in pedidosMesa:
                detalles = pedido.detalles.all()
                for detalle in detalles:
                    productosData.append({
                        "detalleId": detalle.id,
                        "pedidoId": pedido.id,
                        "nombreOrden": pedido.nombreOrden,
                        "fechaPedido": pedido.fecha,
                        "productoId": detalle.producto.id if detalle.producto else None,
                        "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                        "cantidad": detalle.cantidad,
                        "precioUnitario": float(detalle.producto.precio) if detalle.producto else 0,
                        "observaciones": detalle.observaciones,
                        "statusDetalle": detalle.status,
                    })
            mesasData.append({
                "numeroMesa": mesa.numeroMesa,
                "statusMesa": mesa.status,
                "productosPedidos": productosData
            })

        return Response({
            "success": True,
            "mesas": mesasData
        }, status=200)
             
class ActualizarStatusDetalle(APIView):
    def post(self, request, detalle_id):
        detalle = DetallePedido.objects.filter(id=detalle_id).first()
        if not detalle:
            return Response({'error': 'DetallePedido no encontrado'}, status=404)

        status = request.data.get('status')
        if not status:
            return Response({'error': 'El campo status es obligatorio'}, status=400)

        detalle.status = status
        detalle.save()

        return Response({
            'success': True,
            'detalleId': detalle.id,
            'nuevoStatus': detalle.status
        }, status=200)

class obtenerTodosPedidosOrdenes(APIView):
    def get(self, request):
        pedidos = Pedido.objects.all()
        if not pedidos.exists():
            return Response({"message": "No hay pedidos registrados"}, status=200)

        pedidos_data = []
        for pedido in pedidos:
            detalles_data = []
            for detalle in pedido.detalles.all():
                detalles_data.append({
                    "productoId": detalle.producto.id if detalle.producto else None,
                    "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                    "cantidad": detalle.cantidad,
                    "observaciones": detalle.observaciones
                })
            pedidos_data.append({
                "pedidoId": pedido.id,
                "nombreOrden": pedido.nombreOrden,
                "fecha": pedido.fecha,
                "status": pedido.status,
                "detalles": detalles_data
            })

        return Response({
            "success": True,
            "pedidos": pedidos_data
        }, status=200)
        
class TotalVentasPorFecha(APIView):
    def get(self, request):
        fechaStr = request.query_params.get('fecha')
        if not fechaStr:
            return Response({'error': 'La fecha es obligatoria (formato YYYY-MM-DD)'}, status=400)
        try:
            fecha = datetime.strptime(fechaStr, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Usa YYYY-MM-DD'}, status=400)

        pedidos = Pedido.objects.filter(fecha__date=fecha, status='completado')
        total = 0
        for pedido in pedidos:
            for detalle in pedido.detalles.all():
                precio = detalle.producto.precio if detalle.producto else 0
                total += precio * detalle.cantidad

        return Response({'fecha': fechaStr, 'totalVentas': float(total)}, status=200)