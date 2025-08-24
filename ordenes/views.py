
from rest_framework.views import APIView
from rest_framework.response import Response
from ordenes.models import *
from datetime import datetime
from ordenes.models import Pedido
from django.utils import timezone
import pytz
from django.db import transaction


class crearOrden(APIView):
    def post(self, request):
        nombreOrden = request.data.get("nombreOrden")
        mesaId = request.data.get("mesaId")
        productos = request.data.get("productos")
        status = request.data.get("status", "proceso")

        if not nombreOrden or not mesaId or not productos or not status:
            return Response({"error": "Todos los campos son obligatorios"}, status=400)

        # Buscar la mesa y actualizar el status a False (ocupada)
        mesa = Mesa.objects.filter(id=mesaId).first()
        if not mesa:
            return Response({"error": "La mesa especificada no existe"}, status=400)
        mesa.status = False
        mesa.save()

        pedido = Pedido.objects.create(
            nombreOrden=nombreOrden,
            idMesa_id=mesaId,
        )

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
                status=status 
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
                    "detalleId": detalle.id,  # <--- Aquí agregas el id único del detalle del pedido
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
        mesas = Mesa.objects.filter(status=False)  # Solo mesas ocupadas
        mesas_data = []
        
        for mesa in mesas:
            # Solo pedidos que NO estén completados (proceso o cancelado)
            pedidos_activos = mesa.pedido_set.exclude(
                status='completado'
            ).order_by('-fecha')
            
            pedidos_data = []
            for pedido in pedidos_activos:
                detalles = pedido.detalles.all()
                    
                detalles_data = []
                for detalle in detalles:
                    detalles_data.append({
                        "detalleId": detalle.id,
                        "productoId": detalle.producto.id if detalle.producto else None,
                        "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                        "cantidad": detalle.cantidad,
                        "precioUnitario": float(detalle.producto.precio) if detalle.producto else 0,
                        "observaciones": detalle.observaciones,
                        "statusDetalle": detalle.status,
                        "fechaPedido": pedido.fecha,
                        "nombreOrden": pedido.nombreOrden,
                        "pedidoId": pedido.id,
                    })
                
                pedidos_data.append({
                    "pedidoId": pedido.id,
                    "nombreOrden": pedido.nombreOrden,
                    "fechaPedido": pedido.fecha,
                    "statusPedido": pedido.status,  # Nuevo campo
                    "detalles": detalles_data,
                })
            
            # Solo agregar mesa si tiene pedidos activos
            if pedidos_data:
                mesas_data.append({
                    "id": mesa.id,
                    "numeroMesa": mesa.numeroMesa,
                    "status": mesa.status,
                    "pedidos": pedidos_data
                })

        return Response({
            "success": True,
            "mesasOcupadas": mesas_data
        }, status=200)
        

class ObtenerHistorialVentasPorDia(APIView):
    def get(self, request):
        # Obtener la fecha del parámetro (formato: YYYY-MM-DD)
        fecha = request.GET.get('fecha')
        
        if not fecha:
            return Response({'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'}, status=400)
        
        try:
            fecha_parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)
        
        # Obtener TODOS los pedidos completados de esa fecha
        pedidos_del_dia = Pedido.objects.filter(
            fecha__date=fecha_parsed,
            status='completado'
        ).select_related('idMesa').order_by('-fecha')
        
        # Agrupar por mesa
        mesas_dict = {}
        
        for pedido in pedidos_del_dia:
            mesa_id = pedido.idMesa.id
            
            # Si la mesa no está en el dict, agregarla
            if mesa_id not in mesas_dict:
                mesas_dict[mesa_id] = {
                    "id": pedido.idMesa.id,
                    "numeroMesa": pedido.idMesa.numeroMesa,
                    "status": pedido.idMesa.status,
                    "pedidos": []
                }
            
            # Obtener detalles del pedido
            detalles = pedido.detalles.all()
            detalles_data = []
            
            for detalle in detalles:
                detalles_data.append({
                    "detalleId": detalle.id,
                    "productoId": detalle.producto.id if detalle.producto else None,
                    "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
                    "cantidad": detalle.cantidad,
                    "precioUnitario": float(detalle.producto.precio) if detalle.producto else 0,
                    "observaciones": detalle.observaciones,
                    "statusDetalle": detalle.status,
                    "fechaPedido": pedido.fecha,
                    "nombreOrden": pedido.nombreOrden,
                    "pedidoId": pedido.id,
                })
            
            # Agregar el pedido a la mesa correspondiente
            mesas_dict[mesa_id]["pedidos"].append({
                "pedidoId": pedido.id,
                "nombreOrden": pedido.nombreOrden,
                "fechaPedido": pedido.fecha,
                "statusPedido": pedido.status,
                "detalles": detalles_data,
            })
        
        # Convertir el diccionario a lista
        mesas_data = list(mesas_dict.values())

        return Response({
            "success": True,
            "mesasOcupadas": mesas_data
        }, status=200)        

class agregarProductosAPedido(APIView):
    def post(self, request):
        pedidoId = request.data.get("pedidoId")
        productos = request.data.get("productos")
        
        if not pedidoId or not productos:
            return Response({
                "error": "Los campos pedidoId y productos son obligatorios"
            }, status=400)
        
        # Verificar que el pedido existe
        pedido = Pedido.objects.filter(id=pedidoId).first()
        if not pedido:
            return Response({
                "error": "El pedido especificado no existe"
            }, status=400)
        
        productosAgregados = []
        for producto in productos:
            productoId = producto.get("productoId")
            cantidad = producto.get("cantidad", 1)
            observaciones = producto.get("observaciones", "")
            status = producto.get("status", "proceso")
            
            if not productoId:
                continue
                
            # Verificar que el producto existe
            if not productoMenu.objects.filter(id=productoId).exists():
                return Response({
                    "error": f"El producto con ID {productoId} no existe"
                }, status=400)
            
            # Crear el nuevo detalle
            nuevoDetalle = DetallePedido.objects.create(
                pedido=pedido,
                producto_id=productoId,
                cantidad=cantidad,
                observaciones=observaciones,
                status=status
            )
            
            productosAgregados.append({
                "detalleId": nuevoDetalle.id,
                "productoId": productoId,
                "cantidad": cantidad,
                "observaciones": observaciones,
                "status": status
            })
        
        return Response({
            "success": True,
            "pedidoId": pedido.id,
            "nombreOrden": pedido.nombreOrden,
            "productosAgregados": productosAgregados,
            "totalProductosAgregados": len(productosAgregados)
        }, status=201)        
     
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
        
class CompletarYTotalPedido(APIView):
    def post(self, request, pedido_id):
        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            return Response({'error': 'Pedido no encontrado'}, status=404)

        detalles = pedido.detalles.all()
        total = 0

        for detalle in detalles:
            if detalle.producto:  # Verifica que el producto exista (no eliminado)
                subtotal = detalle.producto.precio * detalle.cantidad
                total += subtotal
            detalle.status = "completado"
            detalle.save()

        return Response({
            'success': True,
            'pedidoId': pedido.id,
            'total': total
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
        
class TotalVentasPorRangoFechas(APIView):
    def get(self, request):
        fechaInicio = request.query_params.get('fecha_inicio')
        fechaFin = request.query_params.get('fecha_fin')
        
        if not fechaInicio or not fechaFin:
            return Response({'error': 'Debes proporcionar fecha_inicio y fecha_fin en formato YYYY-MM-DD'}, status=400)

        fechaInicioDate = datetime.strptime(fechaInicio, '%Y-%m-%d')
        fechaFinDate = datetime.strptime(fechaFin, '%Y-%m-%d')

        mexicoTz = pytz.timezone('America/Mexico_City')
        inicioMexico = mexicoTz.localize(datetime.combine(fechaInicioDate.date(), datetime.min.time()))
        inicioUtc = inicioMexico.astimezone(pytz.UTC)
        finMexico = mexicoTz.localize(datetime.combine(fechaFinDate.date(), datetime.max.time()))
        finUtc = finMexico.astimezone(pytz.UTC)
        
        detallesCompletados = DetallePedido.objects.filter(
            pedido__fecha__gte=inicioUtc,
            pedido__fecha__lte=finUtc,
            status='pagado',
            producto__isnull=False
        )

        totalVentas = 0
        for detalle in detallesCompletados:
            precio = detalle.producto.precio if detalle.producto else 0
            totalVentas += precio * detalle.cantidad

        return Response({
            'fecha_inicio': fechaInicio,
            'fecha_fin': fechaFin,
            'totalVentas': float(totalVentas)
        }, status=200)
        
class ActualizarCantidadDetalle(APIView):
    def post(self, request, detalleId):
        detalle = DetallePedido.objects.filter(id=detalleId).select_related('producto', 'pedido').first()
        if not detalle:
            return Response({"error": "DetallePedido no encontrado"}, status=404)

        nueva_cantidad = request.data.get("cantidad")
        if nueva_cantidad is None:
            return Response({"error": "El campo 'cantidad' es obligatorio"}, status=400)

        if not str(nueva_cantidad).isdigit():
            return Response({"error": "La cantidad debe ser un número entero"}, status=400)

        nueva_cantidad = int(nueva_cantidad)
        if nueva_cantidad <= 0:
            return Response({"error": "La cantidad debe ser mayor a 0"}, status=400)

        detalle.cantidad = nueva_cantidad
        detalle.save()

        return Response({
            "success": True,
            "detalleId": detalle.id,
            "productoId": detalle.producto.id if detalle.producto else None,
            "nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
            "cantidad": detalle.cantidad,
            "precioUnitario": float(detalle.producto.precio) if detalle.producto else 0,
            "observaciones": detalle.observaciones,
            "statusDetalle": detalle.status,
            "fechaPedido": detalle.pedido.fecha,
            "nombreOrden": detalle.pedido.nombreOrden,
            "pedidoId": detalle.pedido.id
        }, status=200)
             
class EliminarDetallesDePedido(APIView):
    def delete(self, request, pedidoId):
        # Aquí pedidoId es realmente el ID del detalle que quieres eliminar
        detalle = DetallePedido.objects.filter(id=pedidoId).first()
        if not detalle:
            return Response({'error': 'Detalle de pedido no encontrado'}, status=404)
        
        print(detalle)

        force = request.query_params.get('force')
        force = (str(force).strip().lower() in ('1', 'true', 't', 'yes', 'y', 'si', 'sí'))

        # Verificar si el detalle está en proceso
        if detalle.status == 'proceso' and not force:
            return Response(
                {'error': 'No se puede eliminar el detalle: está en proceso. Use ?force=true si desea forzar.'},
                status=409
            )

        with transaction.atomic():
            # Guardar información antes de eliminar
            pedido_id = detalle.pedido.id
            producto_nombre = detalle.producto.nombre if detalle.producto else "Producto eliminado"
            cantidad = detalle.cantidad
            
            # Eliminar el detalle específico
            detalle.delete()

        return Response({
            'success': True,
            'message': f'Se eliminó el detalle: {cantidad} x {producto_nombre} del pedido {pedido_id}.'
        }, status=200)
           
class EliminarPedidoCompleto(APIView):
    def delete(self, request, idMesa):
        pedido = Pedido.objects.filter(id=idMesa).select_related('idMesa').first()
        if not pedido:
            return Response({'error': 'Pedido no encontrado'}, status=404)

        mesa = pedido.idMesa

        with transaction.atomic():
            # Borra el pedido; DetallePedido se borra por cascada
            pedido.delete()

            # Verifica si la mesa queda sin pedidos
            tiene_pedidos = mesa.pedido_set.exists()
            if not tiene_pedidos and mesa.status is False:
                mesa.status = True
                mesa.save()

        return Response({
            'success': True,
            'message': f'Pedido eliminado correctamente. Mesa {mesa.numeroMesa} {"liberada" if not tiene_pedidos else "permanece ocupada"}.',
            'mesa': {
                'id': mesa.id,
                'numeroMesa': mesa.numeroMesa,
                'status': mesa.status
            }
        }, status=200)