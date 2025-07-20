
from rest_framework.views import APIView
from rest_framework.response import Response

from ordenes.models import *


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
            status=status
        )
        if not pedido:
            return Response({"error": "Error al crear el pedido"}, status=500)

        for producto in productos:
            productoId = producto.get("productoId")
            cantidad = producto.get("cantidad", 1)
            observaciones = producto.get("observaciones", "")
            if not productoId:
                continue
            DetallePedido.objects.create(
                pedido=pedido,
                producto_id=productoId,
                cantidad=cantidad,
                observaciones=observaciones
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
        pedidos = Pedido.objects.obtenerPedidoEnProceso()
        if not pedidos:
            return Response({"message": "No hay pedidos en proceso"}, status=200)
        
        pedidosPorMesa = []
        for pedido in pedidos:
            mesa = pedido.idMesa
            detalles = pedido.detalles.all()
            listaDetalles = []
            for detalle in detalles:
                listaDetalles.append({
                    "productoId": detalle.producto.id if detalle.producto else None,
                    "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                    "cantidad": detalle.cantidad,
                    "observaciones": detalle.observaciones
                })
            pedidoInfo = {
                "pedidoId": pedido.id,
                "nombreOrden": pedido.nombreOrden,
                "fecha": pedido.fecha,
                "status": pedido.status,
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
        
        return Response({
            "success": True,
            "pedidosPorMesa": pedidosPorMesa
        }, status=200)
        
class ObtenerMesasConPedidosAbiertos(APIView):
    def get(self, request):
        mesas = Mesa.objects.obtenerMesasConPedidoAbierto()
        if not mesas:
            return Response({"message": "No hay mesas abiertas"}, status=200)
        
        mesasData = []
        for mesa in mesas:
            pedidosAbiertos = mesa.pedido_set.filter(status='proceso').order_by('fecha')
            pedidosData = []
            for pedido in pedidosAbiertos:
                detalles = pedido.detalles.all()
                detallesData = []
                totalPedido = 0
                for detalle in detalles:
                    precioUnitario = detalle.producto.precio if detalle.producto else 0
                    subtotal = precioUnitario * detalle.cantidad
                    totalPedido += subtotal
                    detallesData.append({
                        "productoId": detalle.producto.id if detalle.producto else None,
                        "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                        "cantidad": detalle.cantidad,
                        "precioUnitario": float(precioUnitario),
                        "subtotal": float(subtotal),
                        "observaciones": detalle.observaciones
                    })
                pedidosData.append({
                    "pedidoId": pedido.id,
                    "nombreOrden": pedido.nombreOrden,
                    "fecha": pedido.fecha,
                    "status": pedido.status,
                    "total": float(totalPedido),
                    "detalles": detallesData
                })
            mesasData.append({
                "numeroMesa": mesa.numeroMesa,
                "status": mesa.status,
                "pedidos": pedidosData
            })
        
        return Response({
            "success": True,
            "mesas": mesasData
        }, status=200)