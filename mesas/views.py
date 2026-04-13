
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction

from mesas.models import Mesa, GrupoMesas
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
		grupo_id = request.data.get('grupoId')

		if grupo_id:
			grupo = GrupoMesas.objects.filter(id=grupo_id).first()
			if not grupo:
				return Response({'error': 'Grupo no encontrado'}, status=404)

			nuevo_status = request.data.get('status')
			if nuevo_status is None:
				return Response({'error': 'El campo status es obligatorio y debe ser true o false.'}, status=400)

			if nuevo_status is True or nuevo_status == "true" or nuevo_status == 1:
				mesas_grupo = Mesa.objects.filter(grupo=grupo)
				for m in mesas_grupo:
					if m.pedido_set.filter(detalles__status="proceso").exists():
						return Response({
							'success': False,
							'message': f'No se puede liberar el grupo porque la mesa {m.numeroMesa} aún tiene productos en proceso.'
						}, status=400)

				with transaction.atomic():
					for m in mesas_grupo:
						m.pedido_set.exclude(status='completado').update(status='completado')
					mesas_info = list(mesas_grupo.values('id', 'numeroMesa'))
					mesas_grupo.update(status=True, grupo=None)
					grupo.delete()

				return Response({
					'success': True,
					'message': 'Grupo de mesas liberado correctamente.',
					'mesas': mesas_info
				}, status=200)

		mesa = Mesa.objects.filter(id=mesa_id).select_related('grupo').first()
		if not mesa:
			return Response({'error': 'Mesa no encontrada'}, status=404)

		nuevo_status = request.data.get('status')
		if nuevo_status is None:
			return Response({'error': 'El campo status es obligatorio y debe ser true o false.'}, status=400)

		if nuevo_status is True or nuevo_status == "true" or nuevo_status == 1:
			if mesa.grupo:
				mesas_grupo = Mesa.objects.filter(grupo=mesa.grupo)
				# Verificar que ninguna mesa del grupo tenga productos en proceso
				for m in mesas_grupo:
					if m.pedido_set.filter(detalles__status="proceso").exists():
						return Response({
							'success': False,
							'message': f'No se puede liberar el grupo porque la mesa {m.numeroMesa} aún tiene productos en proceso.'
						}, status=400)

				with transaction.atomic():
					for m in mesas_grupo:
						m.pedido_set.exclude(status='completado').update(status='completado')
					grupo = mesa.grupo
					mesas_info = list(mesas_grupo.values('id', 'numeroMesa'))
					mesas_grupo.update(status=True, grupo=None)
					grupo.delete()

				return Response({
					'success': True,
					'message': 'Grupo de mesas liberado correctamente.',
					'mesas': mesas_info
				}, status=200)
			else:
				productos_en_proceso = mesa.pedido_set.filter(detalles__status="proceso").exists()
				if productos_en_proceso:
					return Response({
						'success': False,
						'message': f'No se puede liberar la mesa {mesa.numeroMesa} porque aún hay productos en proceso.'
					}, status=400)

				mesa.pedido_set.exclude(status='completado').update(status='completado')
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
		mesas = Mesa.objects.obtenerMesas().select_related('grupo')
		if not mesas:
			return Response({'mensaje': 'No hay mesas registradas'}, status=404)

		resultado = []
		grupos_procesados = {}
		contador_grupo = 1

		for mesa in mesas:
			if mesa.grupo_id:
				if mesa.grupo_id not in grupos_procesados:
					# Primera mesa del grupo: crear la entrada del grupo
					# Usar nombre personalizado si existe, de lo contrario el autogenerado
					nombre_personalizado = mesa.grupo.nombre if mesa.grupo and mesa.grupo.nombre else None
					etiqueta = nombre_personalizado if nombre_personalizado else f'Agrupado {contador_grupo}'
					contador_grupo += 1
					entrada_grupo = {
						'esGrupo': True,
						'grupoId': mesa.grupo_id,
						'etiquetaGrupo': etiqueta,
						'nombrePersonalizado': nombre_personalizado,
						'status': mesa.status,
						'mesas': [{'id': mesa.id, 'numeroMesa': mesa.numeroMesa}]
					}
					grupos_procesados[mesa.grupo_id] = entrada_grupo
					resultado.append(entrada_grupo)
				else:
					# Mesa adicional del mismo grupo: solo agregar a la lista
					grupos_procesados[mesa.grupo_id]['mesas'].append({
						'id': mesa.id,
						'numeroMesa': mesa.numeroMesa
					})
			else:
				resultado.append({
					'esGrupo': False,
					'grupoId': None,
					'etiquetaGrupo': None,
					'id': mesa.id,
					'numeroMesa': mesa.numeroMesa,
					'status': mesa.status,
				})

		return Response(resultado, status=200)


class AtenderMesaCompleta(APIView):
	def post(self, request, mesa_id):
		grupo_id = request.data.get('grupoId')

		if grupo_id:
			grupo = GrupoMesas.objects.filter(id=grupo_id).first()
			if not grupo:
				return Response({'error': 'Grupo no encontrado'}, status=404)
			mesas_a_atender = Mesa.objects.filter(grupo=grupo)
			if not mesas_a_atender.exists():
				return Response({'error': 'El grupo no tiene mesas'}, status=404)
			mesa = mesas_a_atender.first()
		else:
			mesa = Mesa.objects.filter(numeroMesa=mesa_id).select_related('grupo').first()
			if not mesa:
				return Response({'error': 'Mesa no encontrada'}, status=404)
			# Si la mesa pertenece a un grupo, atender todas las mesas del grupo
			if mesa.grupo:
				mesas_a_atender = Mesa.objects.filter(grupo=mesa.grupo)
			else:
				mesas_a_atender = Mesa.objects.filter(id=mesa.id)

		todos_pedidos = Pedido.objects.filter(idMesa__in=mesas_a_atender)
		pedidos_con_detalles_proceso = todos_pedidos.filter(detalles__status='proceso').distinct()

		if not pedidos_con_detalles_proceso.exists():
			return Response({
				'success': True,
				'message': f'La mesa {mesa.numeroMesa} no tiene detalles de pedidos pendientes.',
				'mesa': {'id': mesa.id, 'numeroMesa': mesa.numeroMesa, 'status': mesa.status},
				'grupoId': mesa.grupo_id,
				'resumen': {'pedidosAtendidos': 0, 'totalMesa': 0.0, 'pedidos': []},
			}, status=200)

		resumen_pedidos = []
		total_mesa = 0.0

		with transaction.atomic():
			detalles_en_proceso = DetallePedido.objects.filter(
				pedido__idMesa__in=mesas_a_atender,
				status='proceso'
			)
			detalles_actualizados = detalles_en_proceso.update(status='completado')

			for pedido in pedidos_con_detalles_proceso.select_related('idMesa'):
				qs_detalles = pedido.detalles.all().select_related('producto')
				total_pedido = 0.0
				for d in qs_detalles:
					if d.status != 'cancelado' and d.producto:
						total_pedido += float(d.producto.precio) * d.cantidad
				total_mesa += total_pedido
				resumen_pedidos.append({
					'pedidoId': pedido.id,
					'nombreOrden': pedido.nombreOrden,
					'mesaNumero': pedido.idMesa.numeroMesa,
					'totalPedido': total_pedido,
					'detalles': {
						'total': qs_detalles.count(),
						'completados': qs_detalles.filter(status='completado').count(),
						'cancelados': qs_detalles.filter(status='cancelado').count()
					}
				})

		return Response({
			'success': True,
			'message': f'Se completaron {detalles_actualizados} detalle(s) de {len(resumen_pedidos)} pedido(s).',
			'mesa': {'id': mesa.id, 'numeroMesa': mesa.numeroMesa, 'status': mesa.status},
			'grupoId': mesa.grupo_id,
			'resumen': {
				'pedidosAtendidos': len(resumen_pedidos),
				'totalMesa': total_mesa,
				'pedidos': resumen_pedidos
			}
		}, status=200)


class AgruparMesas(APIView):
	def post(self, request):
		mesa_ids = request.data.get('mesas', [])

		if not mesa_ids or len(mesa_ids) < 2:
			return Response({'error': 'Se necesitan al menos 2 mesas para agrupar'}, status=400)

		mesas = Mesa.objects.filter(id__in=mesa_ids)
		if mesas.count() != len(mesa_ids):
			return Response({'error': 'Una o más mesas no existen'}, status=404)

		mesas_con_grupo = mesas.filter(grupo__isnull=False)
		if mesas_con_grupo.exists():
			numeros = list(mesas_con_grupo.values_list('numeroMesa', flat=True))
			return Response({'error': f'Las mesas {numeros} ya pertenecen a un grupo'}, status=400)

		with transaction.atomic():
			grupo = GrupoMesas.objects.create()
			mesas.update(grupo=grupo, status=False)

		mesas_actualizadas = Mesa.objects.filter(id__in=mesa_ids).values('id', 'numeroMesa', 'status')
		return Response({
			'success': True,
			'grupoId': grupo.id,
			'mesas': list(mesas_actualizadas)
		}, status=201)


class DesagruparMesas(APIView):
	def delete(self, request, grupo_id):
		grupo = GrupoMesas.objects.filter(id=grupo_id).first()
		if not grupo:
			return Response({'error': 'Grupo no encontrado'}, status=404)

		mesas = Mesa.objects.filter(grupo=grupo)
		mesas_info = list(mesas.values('id', 'numeroMesa'))

		with transaction.atomic():
			mesas.update(grupo=None)
			grupo.delete()

		return Response({
			'success': True,
			'message': f'Grupo {grupo_id} disuelto correctamente.',
			'mesas': mesas_info
		}, status=200)

class RenombrarGrupo(APIView):
	def put(self, request, grupo_id):
		grupo = GrupoMesas.objects.filter(id=grupo_id).first()
		if not grupo:
			return Response({'error': 'Grupo no encontrado'}, status=404)

		nuevo_nombre = request.data.get('nombre', '').strip()
		if not nuevo_nombre:
			return Response({'error': 'El campo nombre es obligatorio'}, status=400)

		grupo.nombre = nuevo_nombre
		grupo.save()

		mesas_del_grupo = list(Mesa.objects.filter(grupo=grupo).values('id', 'numeroMesa'))

		return Response({
			'success': True,
			'grupoId': grupo.id,
			'nombre': grupo.nombre,
			'mesas': mesas_del_grupo
		}, status=200)
