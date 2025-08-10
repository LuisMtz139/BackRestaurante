
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

from mesas.models import Mesa
from ordenes.models import *


class CrearMesa(APIView):
    def post(self, request):
        numeroMesa = request.data.get('numeroMesa')

        if not numeroMesa:
            return Response('El número de mesa es obligatorio', status=400)

        obtenerMesa = Mesa.objects.verificarExistenciaMesa(numeroMesa)
        
        if not obtenerMesa:
            return Response('La mesa ya existe', status=400)

        return Response({
            'id': obtenerMesa.id,
            'numeroMesa': obtenerMesa.numeroMesa,
            'status': obtenerMesa.status,
        }, status=201)
        
class EliminarMesa(APIView):
    def delete(self, request, id):
        if not id:
            return Response({'error': 'El ID es obligatorio'}, status=400)

        mesa = Mesa.objects.obtenerMesaPorId(id)
        if not mesa:
            return Response({'error': 'Mesa no encontrada'}, status=404)

        mesa.delete()
        return Response({'mensaje': 'Mesa eliminada correctamente'}, status=200)
  
class ActualizarStatusMesa(APIView):
    def post(self, request, mesa_id):
        mesa = Mesa.objects.filter(id=mesa_id).first()
        if not mesa:
            return Response({'error': 'Mesa no encontrada'}, status=404)
        
        nuevo_status = request.data.get('status')
        if nuevo_status is None:
            return Response({'error': 'El campo status es obligatorio y debe ser true o false.'}, status=400)
        
        # Si se quiere cambiar a status=True (liberar la mesa)
        if nuevo_status is True or nuevo_status == "true" or nuevo_status == 1:
            productos_en_proceso = mesa.pedido_set.filter(detalles__status="proceso").exists()
            if productos_en_proceso:
                return Response({
                    'success': False,
                    'message': f'No se puede liberar la mesa {mesa.numeroMesa} porque aún hay productos en proceso.'
                }, status=400)
            
            # Marcar todos los pedidos de la mesa como completados
            mesa.pedido_set.exclude(status='completado').update(status='completado')
            
            # Liberar la mesa
            mesa.status = True
            mesa.save()
            
            return Response({
                'success': True,
                'message': f'Mesa {mesa.numeroMesa} liberada correctamente.',
                'mesa': {
                    'id': mesa.id,
                    'numeroMesa': mesa.numeroMesa,
                    'status': mesa.status
                }
            }, status=200)
        
        # Si se quiere cambiar a status=False (ocupar la mesa)
        else:
            mesa.status = bool(nuevo_status)
            mesa.save()
            return Response({
                'success': True,
                'message': f'Status de la mesa {mesa.numeroMesa} actualizado correctamente.',
                'mesa': {
                    'id': mesa.id,
                    'numeroMesa': mesa.numeroMesa,
                    'status': mesa.status
                }
            }, status=200)
class modificarStatusMesa(APIView):
    def put(self, request, id):
        if not id:
            return Response({'error': 'El ID es obligatorio'}, status=400)

        mesa = Mesa.objects.obtenerMesaPorId(id)
        if not mesa:
            return Response({'error': 'Mesa no encontrada'}, status=404)

        status = request.data.get('status')
        if status is None:
            return Response({'error': 'El estado es obligatorio'}, status=400)

        mesa.status = status
        mesa.save()

        return Response({
            'numeroMesa': mesa.numeroMesa,
            'status': mesa.status,
        }, status=200)
        
class lsitarMesasStatus(APIView):
    def get(self, request):
        mesas = Mesa.objects.obtenerMesas()
        if not mesas:
            return Response({'mensaje': 'No hay mesas registradas'}, status=404)

        mesas_data = [{'id': mesa.id, 'numeroMesa': mesa.numeroMesa, 'status': mesa.status} for mesa in mesas]
        return Response(mesas_data, status=200)
    
    
class AtenderMesaCompleta(APIView):
    def post(self, request, mesa_id):
        
        mesa = Mesa.objects.filter(numeroMesa=mesa_id).first()
        if not mesa:
            return Response({'error': 'Mesa no encontrada'}, status=404)

        todos_pedidos = Pedido.objects.filter(idMesa=mesa)
        
        print(f"Pedidos encontrados para mesa {mesa.numeroMesa}: {todos_pedidos.count()}")
        for p in todos_pedidos:
            print(f"  Pedido {p.id}: {p.status}")
            detalles_proceso = p.detalles.filter(status='proceso')
            print(f"    Detalles en proceso: {detalles_proceso.count()}")

        pedidos_con_detalles_proceso = todos_pedidos.filter(
            detalles__status='proceso'
        ).distinct()
        
        if not pedidos_con_detalles_proceso.exists():
            return Response({
                'success': True,
                'message': f'La mesa {mesa.numeroMesa} no tiene detalles de pedidos pendientes.',
                'mesa': {'id': mesa.id, 'numeroMesa': mesa.numeroMesa, 'status': mesa.status},
                'resumen': {'pedidosAtendidos': 0, 'totalMesa': 0.0, 'pedidos': []},
                'debug': {
                    'totalPedidos': todos_pedidos.count(),
                    'pedidosConDetallesProceso': pedidos_con_detalles_proceso.count()
                }
            }, status=200)

        resumen_pedidos = []
        total_mesa = 0.0

        with transaction.atomic():
            # 4) Obtener todos los detalles en proceso de la mesa
            detalles_en_proceso = DetallePedido.objects.filter(
                pedido__idMesa=mesa,
                status='proceso'
            )
            
            print(f"Detalles en proceso encontrados: {detalles_en_proceso.count()}")
            
            # 5) Actualizar detalles a completado
            detalles_actualizados = detalles_en_proceso.update(status='completado')
            print(f"Detalles actualizados: {detalles_actualizados}")

            # 6) Calcular totales por pedido
            for pedido in pedidos_con_detalles_proceso.select_related('idMesa'):
                qs_detalles = pedido.detalles.all().select_related('producto')
                total_pedido = 0.0

                # Sumar solo no cancelados y con producto válido
                for d in qs_detalles:
                    if d.status != 'cancelado' and d.producto:
                        total_pedido += float(d.producto.precio) * d.cantidad

                total_mesa += total_pedido
                resumen_pedidos.append({
                    'pedidoId': pedido.id,
                    'nombreOrden': pedido.nombreOrden,
                    'totalPedido': total_pedido,
                    'detalles': {
                        'total': qs_detalles.count(),
                        'completados': qs_detalles.filter(status='completado').count(),
                        'cancelados': qs_detalles.filter(status='cancelado').count()
                    }
                })

        return Response({
            'success': True,
            'message': f'Se completaron {detalles_actualizados} detalle(s) de {len(resumen_pedidos)} pedido(s) de la mesa {mesa.numeroMesa}.',
            'mesa': {
                'id': mesa.id,
                'numeroMesa': mesa.numeroMesa,
                'status': mesa.status
            },
            'resumen': {
                'pedidosAtendidos': len(resumen_pedidos),
                'totalMesa': total_mesa,
                'pedidos': resumen_pedidos
            }
        }, status=200)