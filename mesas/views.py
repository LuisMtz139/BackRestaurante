
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
  
class LiberarMesa(APIView):
    def post(self, request, mesa_id):
        mesa = Mesa.objects.filter(id=mesa_id).first()
        if not mesa:
            return Response({'error': 'Mesa no encontrada'}, status=4004)
        
        pedidos_abiertos = Pedido.objects.filter(
            idMesa=mesa,
            detalles__status="proceso"
        ).distinct()

        if pedidos_abiertos.exists():
            return Response({
                'success': False,
                'message': 'No se puede liberar la mesa: Hay pedidos abiertos pendientes en esta mesa.'
            }, status=400)
        
        mesa.status = True
        mesa.save()
        return Response({
            'success': True,
            'message': f'Mesa {mesa.numeroMesa} liberada y disponible.'
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