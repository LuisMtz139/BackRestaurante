
from rest_framework.views import APIView
from rest_framework.response import Response

from mesas.models import Mesa
from ordenes.models import Pedido


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
        
        # Si se quiere cambiar a status=True (abrir la mesa), revisa que no haya productos en proceso
        if nuevo_status is True or nuevo_status == "true" or nuevo_status == 1:
            productos_en_proceso = mesa.pedido_set.filter(detalles__status="proceso").exists()
            if productos_en_proceso:
                return Response({
                    'success': False,
                    'message': f'No se puede poner status=True a la mesa {mesa.numeroMesa} porque aún hay productos en proceso.'
                }, status=400)
        
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