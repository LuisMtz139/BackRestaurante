
from rest_framework.views import APIView
from rest_framework.response import Response
from ordenes.models import *
from datetime import datetime
from ordenes.models import Pedido
from django.utils import timezone
import pytz
from django.db import transaction
from collections import defaultdict
from django.db.models import Sum


class crearOrden(APIView):
	def post(self, request):
		nombreOrden = request.data.get("nombreOrden")
		mesaId = request.data.get("mesaId")
		grupoId = request.data.get("grupoId")
		productos = request.data.get("productos")
		status = request.data.get("status", "proceso")

		if not nombreOrden or not productos or not status:
			return Response({"error": "Todos los campos son obligatorios"}, status=400)

		if not mesaId and not grupoId:
			return Response({"error": "Debes enviar mesaId o grupoId"}, status=400)

		if grupoId:
			# Buscar la primera mesa del grupo para asociar el pedido
			mesa = Mesa.objects.filter(grupo_id=grupoId).select_related('grupo').first()
			if not mesa:
				return Response({"error": "El grupo especificado no existe o no tiene mesas"}, status=400)
			Mesa.objects.filter(grupo_id=grupoId).update(status=False)
		else:
			mesa = Mesa.objects.filter(id=mesaId).select_related('grupo').first()
			if not mesa:
				return Response({"error": "La mesa especificada no existe"}, status=400)
			if mesa.grupo:
				return Response({"error": f"La mesa {mesa.numeroMesa} pertenece al grupo {mesa.grupo_id}. Usa grupoId en lugar de mesaId."}, status=400)
			mesa.status = False
			mesa.save()

		pedido = Pedido.objects.create(
			nombreOrden=nombreOrden,
			idMesa_id=mesa.id,
		)

		for producto in productos:
			productoId = producto.get("productoId")
			cantidad = producto.get("cantidad", 1)
			observaciones = producto.get("observaciones", "")
			if not productoId:
				continue
			# Verifica que el producto exista
			producto_obj = productoMenu.objects.filter(id=productoId).first()
			if not producto_obj:
				return Response({"error": f"El producto con ID {productoId} no existe"}, status=400)
			
			# 🔥 Determinar status según mostrarEnListado
			if producto_obj.mostrarEnListado:
				status_detalle = status  # Usa el status enviado en el request
			else:
				status_detalle = "completado"  # Automáticamente completado
			
			DetallePedido.objects.create(
				pedido=pedido,
				producto_id=productoId,
				cantidad=cantidad,
				observaciones=observaciones,
				status=status_detalle  # 👈 Aquí se aplica la lógica
			)

		return Response({
			"success": True,
			"pedidoId": pedido.id,
			"nombreOrden": pedido.nombreOrden,
			"mesaId": pedido.idMesa_id,
			"grupoId": mesa.grupo_id,
			"productos": productos
		}, status=201)
			
class obtenerListaPedidosPendientes(APIView):
	def get(self, request):
		pedidos = Pedido.objects.all().order_by('fecha').select_related('idMesa__grupo')
		pedidosPorMesa = []

		for pedido in pedidos:
			mesa = pedido.idMesa
			detalles = pedido.detalles.filter(
				status="proceso",
				producto__mostrarEnListado=True
			)

			listaDetalles = []
			for detalle in detalles:
				listaDetalles.append({
					"detalleId": detalle.id,
					"productoId": detalle.producto.id if detalle.producto else None,
					"nombreProducto": detalle.producto.nombre if detalle.producto else "Producto eliminado",
					"cantidad": detalle.cantidad,
					"observaciones": detalle.observaciones,
					"status": detalle.status,
					"mostrarEnListado": detalle.producto.mostrarEnListado if detalle.producto else False,
					"fecha": detalle.fecha,
				})

			if not listaDetalles:
				continue

			pedidoInfo = {
				"pedidoId": pedido.id,
				"nombreOrden": pedido.nombreOrden,
				"fecha": pedido.fecha,
				"mesaNumero": mesa.numeroMesa,
				"detalles": listaDetalles
			}

			if mesa.grupo:
				grupoExistente = next((g for g in pedidosPorMesa if g.get("grupoId") == mesa.grupo_id), None)
				if not grupoExistente:
					mesas_del_grupo = list(Mesa.objects.filter(grupo=mesa.grupo).values('id', 'numeroMesa'))
					nombreGrupo = ", ".join(f"Mesa {m['numeroMesa']}" for m in sorted(mesas_del_grupo, key=lambda m: m['numeroMesa']))
					pedidosPorMesa.append({
						"esGrupo": True,
						"grupoId": mesa.grupo_id,
						"nombreGrupo": nombreGrupo,
						"mesasAgrupadas": mesas_del_grupo,
						"pedidos": [pedidoInfo]
					})
				else:
					grupoExistente["pedidos"].append(pedidoInfo)
			else:
				mesaExistente = next((m for m in pedidosPorMesa if m.get("numeroMesa") == mesa.numeroMesa), None)
				if not mesaExistente:
					pedidosPorMesa.append({
						"esGrupo": False,
						"grupoId": None,
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
  
class cambiarStatusDetallePedido(APIView):
	def post(self, request):
		print(request.data)
		status = request.data['status']
		detalleId = request.data['detalleId']

		detalle = productoMenu.objects.filter(id=detalleId).first()  
  
		if not detalle:
			return Response({'error': 'Pedido no encontrado'}, status=404)

		print(status)
		detalle.mostrarEnListado = status
		detalle.save()

		return Response({
			'detalleId': detalle.id,
			'mostrarEnListado': detalle.mostrarEnListado
		}, status=200)

class ModificarnombreOrden(APIView):
	def post(self, request):
		nuevoNombre = request.data.get('nuevoNombre')
		pedidoId = request.data['pedidoId']
  
		if not pedidoId:
			return Response({'error': 'El pedidoId es obligatorio'}, status=400)

		pedido = Pedido.objects.filter(id=pedidoId).first()
		if not pedido:
			return Response({'error': 'Pedido no encontrado'}, status=404)

		pedido.nombreOrden = nuevoNombre
		pedido.save()

		return Response({
			'success': True,
			'pedidoId': pedido.id,
			'nuevoNombreOrden': pedido.nombreOrden
		}, status=200)
		
class ObtenerTodasLasMesasConProductos(APIView):
	def get(self, request):
		mesas = Mesa.objects.filter(status=False).select_related('grupo')
		mesas_data = []
		grupos_procesados = set()

		for mesa in mesas:
			if mesa.grupo:
				if mesa.grupo_id in grupos_procesados:
					continue
				grupos_procesados.add(mesa.grupo_id)

				mesas_del_grupo = Mesa.objects.filter(grupo=mesa.grupo)
				pedidos_data = []

				for m in mesas_del_grupo:
					pedidos_activos = m.pedido_set.exclude(status='completado').order_by('-fecha')
					for pedido in pedidos_activos:
						detalles = pedido.detalles.all()
						productos_agrupados = defaultdict(lambda: {
							"cantidad": 0, "precioTotal": 0, "detalleId": None,
							"productoId": None, "nombreProducto": "", "precioUnitario": 0,
							"observaciones": "", "statusDetalle": "", "fechaPedido": None,
							"nombreOrden": "", "pedidoId": None, "mesaNumero": None, "statuses": []
						})
						for detalle in detalles:
							if detalle.status == 'cancelado':
								continue
							producto_id = detalle.producto.id if detalle.producto else None
							if productos_agrupados[producto_id]["detalleId"] is None:
								productos_agrupados[producto_id]["detalleId"] = detalle.id
								productos_agrupados[producto_id]["productoId"] = producto_id
								productos_agrupados[producto_id]["nombreProducto"] = detalle.producto.nombre if detalle.producto else "Producto eliminado"
								productos_agrupados[producto_id]["precioUnitario"] = float(detalle.producto.precio) if detalle.producto else 0
								productos_agrupados[producto_id]["observaciones"] = detalle.observaciones
								productos_agrupados[producto_id]["fechaPedido"] = pedido.fecha
								productos_agrupados[producto_id]["nombreOrden"] = pedido.nombreOrden
								productos_agrupados[producto_id]["pedidoId"] = pedido.id
								productos_agrupados[producto_id]["mesaNumero"] = m.numeroMesa
							productos_agrupados[producto_id]["statuses"].append(detalle.status)
							productos_agrupados[producto_id]["cantidad"] += detalle.cantidad
							productos_agrupados[producto_id]["precioTotal"] += float(detalle.producto.precio) * detalle.cantidad if detalle.producto else 0

						detalles_data = []
						for producto in productos_agrupados.values():
							statuses = producto.pop("statuses")
							if "proceso" in statuses or "pendiente" in statuses:
								producto["statusDetalle"] = "proceso"
							elif all(s == "completado" for s in statuses):
								producto["statusDetalle"] = "completado"
							else:
								producto["statusDetalle"] = statuses[0]
							detalles_data.append(producto)

						if detalles_data:
							pedidos_data.append({
								"pedidoId": pedido.id,
								"nombreOrden": pedido.nombreOrden,
								"fechaPedido": pedido.fecha,
								"statusPedido": pedido.status,
								"mesaNumero": m.numeroMesa,
								"mesaId": m.id,
								"detalles": detalles_data,
							})

				if pedidos_data:
					mesas_agrupadas = list(mesas_del_grupo.values('id', 'numeroMesa'))
					nombreGrupo = ", ".join(f"Mesa {m['numeroMesa']}" for m in sorted(mesas_agrupadas, key=lambda m: m['numeroMesa']))

					# Consolidar productos de todos los pedidos del grupo
					consolidado = defaultdict(lambda: {
						"productoId": None, "nombreProducto": "", "precioUnitario": 0,
						"cantidad": 0, "precioTotal": 0, "statuses": []
					})
					for p in pedidos_data:
						for det in p["detalles"]:
							pid = det["productoId"]
							if consolidado[pid]["productoId"] is None:
								consolidado[pid]["productoId"] = det["productoId"]
								consolidado[pid]["nombreProducto"] = det["nombreProducto"]
								consolidado[pid]["precioUnitario"] = det["precioUnitario"]
							consolidado[pid]["cantidad"] += det["cantidad"]
							consolidado[pid]["precioTotal"] += det["precioTotal"]
							consolidado[pid]["statuses"].append(det["statusDetalle"])

					productos_consolidados = []
					for item in consolidado.values():
						statuses = item.pop("statuses")
						if "proceso" in statuses or "pendiente" in statuses:
							item["statusDetalle"] = "proceso"
						elif all(s == "completado" for s in statuses):
							item["statusDetalle"] = "completado"
						else:
							item["statusDetalle"] = statuses[0]
						productos_consolidados.append(item)

					mesas_data.append({
						"esGrupo": True,
						"grupoId": mesa.grupo_id,
						"nombreGrupo": nombreGrupo,
						"mesasAgrupadas": mesas_agrupadas,
						"productosAgrupados": productos_consolidados,
						"pedidos": pedidos_data
					})
			else:
				pedidos_activos = mesa.pedido_set.exclude(status='completado').order_by('-fecha')
				pedidos_data = []
				for pedido in pedidos_activos:
					detalles = pedido.detalles.all()
					productos_agrupados = defaultdict(lambda: {
						"cantidad": 0, "precioTotal": 0, "detalleId": None,
						"productoId": None, "nombreProducto": "", "precioUnitario": 0,
						"observaciones": "", "statusDetalle": "", "fechaPedido": None,
						"nombreOrden": "", "pedidoId": None, "statuses": []
					})
					for detalle in detalles:
						if detalle.status == 'cancelado':
							continue
						producto_id = detalle.producto.id if detalle.producto else None
						if productos_agrupados[producto_id]["detalleId"] is None:
							productos_agrupados[producto_id]["detalleId"] = detalle.id
							productos_agrupados[producto_id]["productoId"] = producto_id
							productos_agrupados[producto_id]["nombreProducto"] = detalle.producto.nombre if detalle.producto else "Producto eliminado"
							productos_agrupados[producto_id]["precioUnitario"] = float(detalle.producto.precio) if detalle.producto else 0
							productos_agrupados[producto_id]["observaciones"] = detalle.observaciones
							productos_agrupados[producto_id]["fechaPedido"] = pedido.fecha
							productos_agrupados[producto_id]["nombreOrden"] = pedido.nombreOrden
							productos_agrupados[producto_id]["pedidoId"] = pedido.id
						productos_agrupados[producto_id]["statuses"].append(detalle.status)
						productos_agrupados[producto_id]["cantidad"] += detalle.cantidad
						productos_agrupados[producto_id]["precioTotal"] += float(detalle.producto.precio) * detalle.cantidad if detalle.producto else 0

					detalles_data = []
					for producto in productos_agrupados.values():
						statuses = producto.pop("statuses")
						if "proceso" in statuses or "pendiente" in statuses:
							producto["statusDetalle"] = "proceso"
						elif all(s == "completado" for s in statuses):
							producto["statusDetalle"] = "completado"
						else:
							producto["statusDetalle"] = statuses[0]
						detalles_data.append(producto)

					if detalles_data:
						pedidos_data.append({
							"pedidoId": pedido.id,
							"nombreOrden": pedido.nombreOrden,
							"fechaPedido": pedido.fecha,
							"statusPedido": pedido.status,
							"detalles": detalles_data,
						})

				if pedidos_data:
					consolidado = defaultdict(lambda: {
						"productoId": None, "nombreProducto": "", "precioUnitario": 0,
						"cantidad": 0, "precioTotal": 0, "statuses": []
					})
					for p in pedidos_data:
						for det in p["detalles"]:
							pid = det["productoId"]
							if consolidado[pid]["productoId"] is None:
								consolidado[pid]["productoId"] = det["productoId"]
								consolidado[pid]["nombreProducto"] = det["nombreProducto"]
								consolidado[pid]["precioUnitario"] = det["precioUnitario"]
							consolidado[pid]["cantidad"] += det["cantidad"]
							consolidado[pid]["precioTotal"] += det["precioTotal"]
							consolidado[pid]["statuses"].append(det["statusDetalle"])

					productos_consolidados = []
					for item in consolidado.values():
						statuses = item.pop("statuses")
						if "proceso" in statuses or "pendiente" in statuses:
							item["statusDetalle"] = "proceso"
						elif all(s == "completado" for s in statuses):
							item["statusDetalle"] = "completado"
						else:
							item["statusDetalle"] = statuses[0]
						productos_consolidados.append(item)

					mesas_data.append({
						"esGrupo": False,
						"grupoId": None,
						"id": mesa.id,
						"numeroMesa": mesa.numeroMesa,
						"status": mesa.status,
						"productosAgrupados": productos_consolidados,
						"pedidos": pedidos_data
					})

		return Response({
			"success": True,
			"mesasOcupadas": mesas_data
		}, status=200)

class ObtenerHistorialVentasPorDia(APIView):
	def get(self, request):
		fecha = request.GET.get('fecha')
		page = int(request.GET.get('page', 1))
		page_size = int(request.GET.get('page_size', 10))

		if not fecha:
			return Response({'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'}, status=400)

		try:
			fecha_parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
		except ValueError:
			return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)

		# 1. Traer TODOS los pedidos del día completados
		pedidos_del_dia = Pedido.objects.filter(
			fecha__date=fecha_parsed,
			status='completado'
		).select_related('idMesa').order_by('-fecha')

		# 2. Agrupar pedidos por mesa (sin paginar aún)
		mesas_dict = {}
		for pedido in pedidos_del_dia:
			mesa_id = pedido.idMesa.id
			if mesa_id not in mesas_dict:
				mesas_dict[mesa_id] = {
					"id": pedido.idMesa.id,
					"numeroMesa": pedido.idMesa.numeroMesa,
					"status": pedido.idMesa.status,
					"pedidos": []
				}

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
			mesas_dict[mesa_id]["pedidos"].append({
				"pedidoId": pedido.id,
				"nombreOrden": pedido.nombreOrden,
				"fechaPedido": pedido.fecha,
				"statusPedido": pedido.status,
				"detalles": detalles_data,
			})

		# 3. Convertir a lista y ORDENAR por id de mesa
		mesas_data = sorted(list(mesas_dict.values()), key=lambda x: x["id"])

		# 4. Paginar la lista de mesas
		total_mesas = len(mesas_data)
		start = (page - 1) * page_size
		end = start + page_size
		mesas_paginadas = mesas_data[start:end]

		total_pages = (total_mesas + page_size - 1) // page_size
		has_next = page < total_pages
		has_previous = page > 1

		return Response({
			"success": True,
			"mesasOcupadas": mesas_paginadas,
			"pagination": {
				"current_page": page,
				"page_size": page_size,
				"total_mesas": total_mesas,
				"total_pages": total_pages,
				"has_next": has_next,
				"has_previous": has_previous
			}
		}, status=200)
		
class agregarProductosAPedido(APIView):
	def post(self, request):
		pedidoId = request.data.get("pedidoId")
		mesaId = request.data.get("mesaId")
		grupoId = request.data.get("grupoId")
		productos = request.data.get("productos")

		if not productos:
			return Response({"error": "El campo productos es obligatorio"}, status=400)

		if not pedidoId and not mesaId and not grupoId:
			return Response({"error": "Debes enviar pedidoId, mesaId o grupoId"}, status=400)

		if pedidoId:
			pedido = Pedido.objects.filter(id=pedidoId).first()
			if not pedido:
				return Response({"error": "El pedido especificado no existe"}, status=404)
		else:
			if grupoId:
				mesa = Mesa.objects.filter(grupo_id=grupoId).select_related('grupo').first()
				if not mesa:
					return Response({"error": "El grupo especificado no existe o no tiene mesas"}, status=400)
				# Buscar el pedido activo más reciente del grupo
				pedido = Pedido.objects.filter(
					idMesa__grupo_id=grupoId
				).exclude(status='completado').order_by('-fecha').first()
			else:
				mesa = Mesa.objects.filter(id=mesaId).select_related('grupo').first()
				if not mesa:
					return Response({"error": "La mesa especificada no existe"}, status=400)
				if mesa.grupo:
					return Response({"error": f"La mesa {mesa.numeroMesa} pertenece al grupo {mesa.grupo_id}. Usa grupoId en lugar de mesaId."}, status=400)
				# Buscar el pedido activo más reciente de la mesa
				pedido = Pedido.objects.filter(
					idMesa_id=mesaId
				).exclude(status='completado').order_by('-fecha').first()

			if not pedido:
				return Response({"error": "No hay pedido activo para la mesa/grupo especificado"}, status=404)
		
		productosAgregados = []
		for producto in productos:
			productoId = producto.get("productoId")
			cantidad = producto.get("cantidad", 1)
			observaciones = producto.get("observaciones", "")
			status = producto. get("status", "proceso")
			
			if not productoId:
				continue
				
			# Verificar que el producto existe
			producto_obj = productoMenu.objects.filter(id=productoId).first()
			if not producto_obj:
				return Response({
					"error": f"El producto con ID {productoId} no existe"
				}, status=400)
			
			# 🔥 Determinar status según mostrarEnListado
			if producto_obj.mostrarEnListado:
				status_detalle = status  # Usa el status enviado en el request
			else:
				status_detalle = "completado"  # Automáticamente completado
			
			# Crear el nuevo detalle
			nuevoDetalle = DetallePedido.objects.create(
				pedido=pedido,
				producto_id=productoId,
				cantidad=cantidad,
				observaciones=observaciones,
				status=status_detalle  # 👈 Aquí se aplica la lógica
			)
			
			productosAgregados.append({
				"detalleId": nuevoDetalle.id,
				"productoId": productoId,
				"cantidad": cantidad,
				"observaciones": observaciones,
				"status": status_detalle  # 👈 Retornar el status correcto
			})
		
		return Response({
			"success":  True,
			"pedidoId": pedido.id,
			"nombreOrden": pedido.nombreOrden,
			"productosAgregados": productosAgregados,
			"totalProductosAgregados": len(productosAgregados)
		}, status=201)     
	
 
class ActualizarStatusDetalle(APIView):
	def post(self, request, detalle_id=None):
		status = request.data.get('status')
		if not status:
			return Response({'error': 'El campo status es obligatorio'}, status=400)
		
		# Validar que el status sea válido
		if status not in ['proceso', 'completado', 'cancelado', 'pagado']:
			return Response({'error': 'Status inválido'}, status=400)

		# Verificar si se envió un array de IDs en el JSON
		id_detalle_array = request.data.get('idDetalle', [])
		completar_todos = request.data.get('completarTodos', False)
		
		# Si se envió idDetalle como array, usar esos IDs
		if id_detalle_array and isinstance(id_detalle_array, list):
			# Caso múltiples detalles
			detalles = DetallePedido.objects.filter(id__in=id_detalle_array)
			
			if not detalles.exists():
				return Response({'error': 'No se encontraron los detalles especificados'}, status=404)
			
			# Actualizar todos los detalles del array
			detalles_actualizados_count = 0
			pedido = None
			
			for detalle in detalles:
				if detalle.status != 'cancelado':
					detalle.status = status
					detalle.save()
					detalles_actualizados_count += 1
					if not pedido:
						pedido = detalle.pedido
			
			if not pedido:
				return Response({'error': 'No hay detalles válidos para actualizar'}, status=404)
			
			return Response({
				'success': True,
				'idsActualizados': id_detalle_array,
				'pedidoId': pedido.id,
				'mesaId': pedido.idMesa.id,
				'numeroMesa': pedido.idMesa.numeroMesa,
				'nuevoStatus': status,
				'detallesActualizados': detalles_actualizados_count,
				'statusPedido': pedido.status,
				'mensaje': f'Se actualizaron {detalles_actualizados_count} detalles'
			}, status=200)
		
		# Si no se envió array, usar el detalle_id de la URL (comportamiento original)
		if not detalle_id:
			return Response({'error': 'Debe proporcionar detalle_id en la URL o idDetalle en el JSON'}, status=400)
		
		# Buscar el detalle
		detalle = DetallePedido.objects.filter(id=detalle_id).first()
		if not detalle:
			return Response({'error': 'DetallePedido no encontrado'}, status=404)
		
		pedido = detalle.pedido
		producto_id = detalle.producto.id if detalle.producto else None
		
		if completar_todos and producto_id:
			# Caso 1: Actualizar TODOS los detalles del mismo producto en el pedido
			detalles_actualizados = DetallePedido.objects.filter(
				pedido=pedido,
				producto_id=producto_id
			).exclude(status='cancelado').update(status=status)
			
			mensaje = f'Se actualizaron {detalles_actualizados} detalles del producto {detalle.producto.nombre}'
		else:
			# Caso 2: Solo actualizar el detalle específico
			detalle.status = status
			detalle.save()
			detalles_actualizados = 1
			mensaje = f'Se actualizó el detalle {detalle_id}'
		
		# EL PEDIDO SIEMPRE SE MANTIENE EN "proceso"
		# No cambiamos el status del pedido automáticamente
		
		return Response({
			'success': True,
			'detalleId': detalle.id,
			'pedidoId': pedido.id,
			'mesaId': pedido.idMesa.id,
			'numeroMesa': pedido.idMesa.numeroMesa,
			'nuevoStatus': status,
			'detallesActualizados': detalles_actualizados,
			'statusPedido': pedido.status,
			'mensaje': mensaje
		}, status=200)
		
class CompletarYTotalPedido(APIView):
	def post(self, request, pedido_id):
		pedido = Pedido.objects.filter(id=pedido_id).select_related('idMesa__grupo').first()
		if not pedido:
			return Response({'error': 'Pedido no encontrado'}, status=404)

		mesa = pedido.idMesa
		detalles = pedido.detalles.all()
		total = 0

		for detalle in detalles:
			if detalle.producto:
				subtotal = detalle.producto.precio * detalle.cantidad
				total += subtotal
			detalle.status = "completado"
			detalle.save()

		# Si la mesa pertenece a un grupo, sumar todos los pedidos del grupo
		if mesa.grupo:
			otros_pedidos = Pedido.objects.filter(
				idMesa__grupo=mesa.grupo
			).exclude(id=pedido_id).prefetch_related('detalles__producto')
			for p in otros_pedidos:
				for d in p.detalles.all():
					if d.producto and d.status != 'cancelado':
						total += float(d.producto.precio) * d.cantidad

		return Response({
			'success': True,
			'pedidoId': pedido.id,
			'grupoId': mesa.grupo_id,
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
		detalle = DetallePedido. objects.filter(id=detalleId).select_related('producto', 'pedido').first()
		if not detalle:
			return Response({"error": "DetallePedido no encontrado"}, status=404)

		cantidad_cambio = request.data. get("cantidad")
		if cantidad_cambio is None:
			return Response({"error": "El campo 'cantidad' es obligatorio"}, status=400)

		try:
			cantidad_cambio = int(cantidad_cambio)
		except (ValueError, TypeError):
			return Response({"error": "La cantidad debe ser un número entero"}, status=400)

		if cantidad_cambio == 0:
			return Response({"error": "La cantidad no puede ser 0"}, status=400)

		# Calcular cantidad actual del producto en este pedido
		cantidad_actual = DetallePedido.objects.filter(
			pedido=detalle.pedido,
			producto=detalle.producto
		).aggregate(total=Sum('cantidad'))['total'] or 0

		# CASO 1: Agregar cantidad (positivo)
		if cantidad_cambio > 0:
			# 🔥 Determinar status según mostrarEnListado
			if detalle.producto and detalle.producto.mostrarEnListado:
				status_detalle = 'proceso'
			else: 
				status_detalle = 'completado'
			
			nuevo_detalle = DetallePedido.objects.create(
				pedido=detalle.pedido,
				producto=detalle.producto,
				cantidad=cantidad_cambio,
				observaciones=detalle.observaciones,
				status=status_detalle  # 👈 Aquí se aplica la lógica
			)

			cantidad_total = DetallePedido.objects. filter(
				pedido=detalle.pedido,
				producto=detalle.producto
			).aggregate(total=Sum('cantidad'))['total'] or 0

			return Response({
				"success":  True,
				"accion":  "agregado",
				"detalleId": nuevo_detalle.id,
				"productoId": nuevo_detalle.producto.id if nuevo_detalle. producto else None,
				"nombreProducto": nuevo_detalle. producto.nombre if nuevo_detalle.producto else "Producto eliminado",
				"cantidad": nuevo_detalle.cantidad,
				"cantidadTotal": cantidad_total,
				"precioUnitario": float(nuevo_detalle.producto.precio) if nuevo_detalle.producto else 0,
				"observaciones": nuevo_detalle.observaciones,
				"statusDetalle": nuevo_detalle.status,
				"fechaPedido": detalle.pedido.fecha,
				"nombreOrden": detalle.pedido.nombreOrden,
				"pedidoId": detalle. pedido.id
			}, status=200)

		# CASO 2: Eliminar cantidad (negativo)
		else:
			cantidad_a_eliminar = abs(cantidad_cambio)
			
			if cantidad_a_eliminar > cantidad_actual: 
				return Response({
					"error": f"No puedes eliminar {cantidad_a_eliminar} unidades. Solo hay {cantidad_actual} disponibles"
				}, status=400)

			# Obtener detalles más recientes del producto en este pedido
			detalles_producto = DetallePedido.objects.filter(
				pedido=detalle. pedido,
				producto=detalle.producto
			).order_by('-id')  # Más recientes primero

			cantidad_restante = cantidad_a_eliminar
			detalles_eliminados = []

			for det in detalles_producto:
				if cantidad_restante <= 0:
					break

				if det.cantidad <= cantidad_restante:
					# Eliminar el detalle completo
					cantidad_restante -= det.cantidad
					detalles_eliminados.append({
						"detalleId":  det.id,
						"cantidad": det.cantidad
					})
					det.delete()
				else:
					# Reducir la cantidad del detalle
					det. cantidad -= cantidad_restante
					detalles_eliminados.append({
						"detalleId": det.id,
						"cantidadReducida": cantidad_restante
					})
					det.save()
					cantidad_restante = 0

			# Calcular cantidad total después de eliminar
			cantidad_total = DetallePedido.objects.filter(
				pedido=detalle. pedido,
				producto=detalle.producto
			).aggregate(total=Sum('cantidad'))['total'] or 0

			return Response({
				"success": True,
				"accion": "eliminado",
				"productoId": detalle.producto.id if detalle.producto else None,
				"nombreProducto": detalle.producto.nombre if detalle. producto else "Producto eliminado",
				"cantidadEliminada": cantidad_a_eliminar,
				"cantidadTotal": cantidad_total,
				"detallesAfectados":  detalles_eliminados,
				"fechaPedido": detalle.pedido.fecha,
				"nombreOrden": detalle.pedido.nombreOrden,
				"pedidoId":  detalle.pedido.id
			}, status=200)
   
   		
class ModificarCantidadDetalle(APIView):
	def post(self, request, detalleId):
		detalle = DetallePedido.objects.filter(id=detalleId).select_related('producto', 'pedido').first()
		if not detalle:
			return Response({"error": "DetallePedido no encontrado"}, status=404)

		nueva_cantidad = request.data.get("cantidad")
		if nueva_cantidad is None:
			return Response({"error": "El campo 'cantidad' es obligatorio"}, status=400)

		try:
			nueva_cantidad = int(nueva_cantidad)
		except (ValueError, TypeError):
			return Response({"error": "La cantidad debe ser un número entero"}, status=400)

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
		pedido = Pedido.objects.filter(id=idMesa).select_related('idMesa__grupo').first()
		if not pedido:
			return Response({'error': 'Pedido no encontrado'}, status=404)

		mesa = pedido.idMesa

		with transaction.atomic():
			pedido.delete()

			if mesa.grupo:
				mesas_grupo = Mesa.objects.filter(grupo=mesa.grupo)
				grupo_tiene_pedidos = mesas_grupo.filter(pedido__isnull=False).exists()
				if not grupo_tiene_pedidos:
					grupo = mesa.grupo
					mesas_info = list(mesas_grupo.values('id', 'numeroMesa'))
					mesas_grupo.update(status=True, grupo=None)
					grupo.delete()
					return Response({
						'success': True,
						'message': 'Pedido eliminado. Grupo disuelto y mesas liberadas.',
						'mesasLiberadas': mesas_info
					}, status=200)
				return Response({
					'success': True,
					'message': 'Pedido eliminado. El grupo aún tiene pedidos activos.',
				}, status=200)
			else:
				tiene_pedidos = mesa.pedido_set.exists()
				if not tiene_pedidos and mesa.status is False:
					mesa.status = True
					mesa.save()

		return Response({
			'success': True,
			'message': f'Pedido eliminado correctamente. Mesa {mesa.numeroMesa} {"liberada" if not mesa.pedido_set.exists() else "permanece ocupada"}.',
			'mesa': {
				'id': mesa.id,
				'numeroMesa': mesa.numeroMesa,
				'status': mesa.status
			}
		}, status=200)
  
  
