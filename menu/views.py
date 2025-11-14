from rest_framework.views import APIView
from rest_framework.response import Response
from menu.manager import ProcesosMenu
from menu.models import  *
import base64
from django.db.models import Sum, Q, F
from datetime import datetime
from ordenes.models import *


#categoria menu
class CrearCategoriaMenu(APIView):
	def post(self, request):
		nombre = request.data.get('nombre')
		descripcion = request.data.get('descripcion')

		if not nombre or not descripcion:
			return Response('El nombre es obligatorio', status=400)
		
		categoriaValida = CategoriaMenu.objects.verificarExistenciaCategoria(nombre, descripcion)
		if not categoriaValida:
			categoria = CategoriaMenu.objects.create(
			nombreCategoria=nombre,
			descripcion=descripcion
			)
		else:
			return Response('La categoría ya existe', status=400)
			

		return Response({
			'id': categoria.id,
			'nombreCategoria': categoria.nombreCategoria,
			'descripcion': categoria.descripcion,
		}, status=201)
		
class eliminarCategoriaMenu(APIView):
	def delete(self, request, id):
		if not id:
			return Response({'error': 'El ID es obligatorio'}, status=400)
		
		categoria = CategoriaMenu.objects.verificarExistenciaCategoriaPorId(id)
		if not categoria:
			return Response({'error': 'Categoría no encontrada'}, status=404)

		categoria.delete()
		return Response({'mensaje': 'Categoría eliminada correctamente'}, status=200)

class modificarCategoriaMenu(APIView):
	def put(self, request, id):
		nombre = request.data.get('nombre')
		descripcion = request.data.get('descripcion')

		if not id:
			return Response('El ID es obligatorio', status=400)
		
		if not nombre or not descripcion:
			return Response('Todos los campos son obligatorios', status=400)

		categoria  = CategoriaMenu.objects.verificarExistenciaCategoriaPorId(id)
		
		if categoria is None:
			return Response('Categoría no encontrada', status=404)
		
		categoria.nombreCategoria = nombre
		categoria.descripcion = descripcion
		categoria.save()

		return Response({
			'id': categoria.id,
			'nombreCategoria': categoria.nombreCategoria,
			'descripcion': categoria.descripcion,
		}, status=200)

class listarCategorias(APIView):
	def get(self, request):
		categorias = CategoriaMenu.objects.obtenerCategorias()
		
		if categorias is None:
			return Response('No hay categorías disponibles', status=404)
		
		serializer = []
		for categoria in categorias:
			serializer.append({
				'id': categoria.id,
				'nombreCategoria': categoria.nombreCategoria,
				'descripcion': categoria.descripcion,
				'status': categoria.status,
			})
		return Response(serializer, status=200)

class actualizarOrdenCategoriaMenu(APIView):
	def put(self, request, idCategoriaMenu):
		
		categoria = CategoriaMenu.objects.filter(id=idCategoriaMenu).first()
		if not categoria:
			return Response({'error': 'Categoría no encontrada'}, status=404)
		
		nuevo_orden = request.data.get('ordenMenu')
		if nuevo_orden is None:
			return Response({'error': 'El campo ordenMenu es requerido'}, status=400)
		
		if not isinstance(nuevo_orden, int) and not str(nuevo_orden).isdigit():
			return Response({'error': 'El ordenMenu debe ser un número entero'}, status=400)
		
		categoria.ordenMenu = int(nuevo_orden)
		categoria.save()
		
		return Response({
			'success': True,
			'categoria': {
				'id': categoria.id,
				'nombreCategoria': categoria.nombreCategoria,
				'ordenMenu': categoria.ordenMenu,
				'descripcion': categoria.descripcion,
				'status': categoria.status
			}
		}, status=200)

class obtenerTotalesVentasReales(APIView):
	def get(self, request):
		# Solo recibir UNA fecha específica
		fecha = request.GET.get('fecha')  # Solo 'fecha', no rango
		
		if not fecha:
			return Response({'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'}, status=400)
		
		try:
			fecha_parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
		except ValueError:
			return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)
		
		# Filtro para UN DÍA ESPECÍFICO únicamente
		detalles_base = DetallePedido.objects.filter(
			pedido__fecha__date=fecha_parsed,  # Solo ESE día exacto
			pedido__status='completado',
			status='pagado'  # Solo productos pagados, no cancelados
		)
		
		if not detalles_base.exists():
			return Response({
				'menuPrincipal': {'total': 0, 'cantidad': 0},
				'desechables': {'total': 0, 'cantidad': 0},
				'pan': {'total': 0, 'cantidad': 0},
				'extras': {'total': 0, 'cantidad': 0},
				'bebidas': {'total': 0, 'cantidad': 0},
				'cafe': {'total': 0, 'cantidad': 0},
				'postres': {'total': 0, 'cantidad': 0},
				'totalGeneral': {'total': 0, 'cantidad': 0}
			}, status=200)
		
		# Categorías principales
		categorias_principales = [1, 3, 7, 8]
		
		# MENU PRINCIPAL - total y cantidad
		principales_data = detalles_base.filter(
			producto__categoria_id__in=categorias_principales
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_principales = principales_data['total'] or 0
		cantidad_principales = principales_data['cantidad'] or 0
		
		# DESECHABLES - total y cantidad
		desechables_data = detalles_base.filter(
			producto_id=60
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_desechables = desechables_data['total'] or 0
		cantidad_desechables = desechables_data['cantidad'] or 0
		
		# PAN - total y cantidad
		pan_data = detalles_base.filter(
			producto_id=58
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_pan = pan_data['total'] or 0
		cantidad_pan = pan_data['cantidad'] or 0
		
		# EXTRAS - total y cantidad (excluyendo pan y desechables)
		productos_excluir = [58, 60]
		extras_data = detalles_base.filter(
			producto__categoria__nombreCategoria='EXTRAS'
		).exclude(
			producto_id__in=productos_excluir
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_extras = extras_data['total'] or 0
		cantidad_extras = extras_data['cantidad'] or 0
		
		# BEBIDAS SIN CAFÉ - total y cantidad
		bebidas_data = detalles_base.filter(
			producto__categoria__nombreCategoria='BEBIDAS'
		).exclude(
			producto_id=39  # Excluir café
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_bebidas = bebidas_data['total'] or 0
		cantidad_bebidas = bebidas_data['cantidad'] or 0
		
		# CAFÉ - total y cantidad
		cafe_data = detalles_base.filter(
			producto_id=39  # Solo café
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_cafe = cafe_data['total'] or 0
		cantidad_cafe = cafe_data['cantidad'] or 0
		
		# POSTRES - total y cantidad
		postres_data = detalles_base.filter(
			producto__categoria__nombreCategoria='POSTRES'
		).aggregate(
			total=Sum(F('cantidad') * F('producto__precio')),
			cantidad=Sum('cantidad')
		)
		total_postres = postres_data['total'] or 0
		cantidad_postres = postres_data['cantidad'] or 0
		
		# TOTALES GENERALES
		total_general = total_principales + total_desechables + total_pan + total_extras + total_bebidas + total_cafe + total_postres
		cantidad_general = cantidad_principales + cantidad_desechables + cantidad_pan + cantidad_extras + cantidad_bebidas + cantidad_cafe + cantidad_postres
		
		return Response({
			'menuPrincipal': {
				'total': total_principales,
				'cantidad': cantidad_principales
			},
			'desechables': {
				'total': total_desechables,
				'cantidad': cantidad_desechables
			},
			'pan': {
				'total': total_pan,
				'cantidad': cantidad_pan
			},
			'extras': {
				'total': total_extras,
				'cantidad': cantidad_extras
			},
			'bebidas': {
				'total': total_bebidas,
				'cantidad': cantidad_bebidas
			},
			'cafe': {
				'total': total_cafe,
				'cantidad': cantidad_cafe
			},
			'postres': {
				'total': total_postres,
				'cantidad': cantidad_postres
			},
			'totalGeneral': {
				'total': total_general,
				'cantidad': cantidad_general
			}
		}, status=200)
# Menu
class CrearMenu(APIView):
	def post(self, request):
		nombre = request.POST.get('nombre')
		descripcion = request.POST.get('descripcion')
		precio = request.POST.get('precio')
		tiempoPreparacion = request.POST.get('tiempoPreparacion')
		categoriaId = request.POST.get('categoriaId')

		imagen_file = request.FILES.get('imagen')
		if imagen_file is not None:
			imagen = base64.b64encode(imagen_file.read()).decode()
		else:
			imagen = request.POST.get('imagen')


		if not nombre or not descripcion or not precio:
			return Response('Todos los campos son obligatorios', status=400)
		if not categoriaId:
			return Response('La categoría es obligatoria', status=400)

		categoria = CategoriaMenu.objects.validarExistenciaCategoria(categoriaId)
		if not categoria:
			return Response('Categoría no encontrada', status=404)

		producto = productoMenu.objects.create(
			nombre=nombre,
			descripcion=descripcion,
			precio=precio,
			tiempoPreparacion=tiempoPreparacion,
			imagen=imagen,
			categoria=categoria,
		)

		return Response({
			'id': producto.id,
			'nombre': producto.nombre,
			'descripcion': producto.descripcion,
			'precio': str(producto.precio),
			'tiempoPreparacion': producto.tiempoPreparacion,
			'imagen': producto.imagen,
			'categoria': producto.categoria.nombreCategoria if producto.categoria else None,
		}, status=201)
			
class eliminarMenu(APIView):
	def delete(self, request, id):
		if not id:
			return Response({'error': 'El ID es obligatorio'}, status=400)

		producto = productoMenu.objects.eliminarMenu(id)
		if not producto:
			return Response({'error': 'Producto no encontrado'}, status=404)
		
		return Response({'mensaje': 'Producto eliminado correctamente'}, status=200)
	
class ModificarMenu(APIView):
	def put(self, request, id):
		if not id:
			return Response({'error': 'El ID es obligatorio'}, status=400)

		producto = productoMenu.objects.filter(id=id).first()
		if not producto:
			return Response({'error': 'Producto no encontrado'}, status=404)

		nombre = request.POST.get('nombre')
		descripcion = request.POST.get('descripcion')
		precio = request.POST.get('precio')
		tiempo_preparacion = request.POST.get('tiempoPreparacion')
		categoria_id = request.POST.get('categoriaId')

		imagen_file = request.FILES.get('imagen')
		if imagen_file is not None:
			imagen = base64.b64encode(imagen_file.read()).decode()
		else:
			imagen = request.POST.get('imagen')

		if nombre:
			producto.nombre = nombre
		if descripcion:
			producto.descripcion = descripcion
		if precio:
			producto.precio = precio
		if tiempo_preparacion:
			producto.tiempoPreparacion = tiempo_preparacion
		if imagen:
			producto.imagen = imagen
		if categoria_id:
			try:
				categoria = CategoriaMenu.objects.get(id=categoria_id)
				producto.categoria = categoria
			except CategoriaMenu.DoesNotExist:
				return Response({'error': 'Categoría no encontrada'}, status=404)

		producto.save()

		return Response({
			'id': producto.id,
			'nombre': producto.nombre,
			'descripcion': producto.descripcion,
			'precio': str(producto.precio),
			'tiempoPreparacion': producto.tiempoPreparacion,
			'imagen': producto.imagen,
			'categoria': producto.categoria.id if producto.categoria else None,
		}, status=200)
		
class listarMenuPorCategoria(APIView):
	def get(self, request, categoriaId):
		
		if not categoriaId:
			return Response('El ID de la categoría es obligatorio', status=400)
		
		productos = productoMenu.objects.obtenerMenuPorCategoria(categoriaId)
		
		if not productos:
			return Response('No hay productos disponibles para esta categoría', status=404)
		
		serializer = []
		for producto in productos:
			serializer.append({
				'id': producto.id,
				'nombre': producto.nombre,
				'descripcion': producto.descripcion,
				'precio': str(producto.precio),
				'tiempoPreparacion': producto.tiempoPreparacion,
				'imagen': producto.imagen,
				'categoria': producto.categoria.nombreCategoria if producto.categoria else None,
			})
		return Response(serializer, status=200)

class listarTodoMenu(APIView):
	def get(self, request):
		productos = productoMenu.objects.listarTodoMenu()
		
		if not productos:
			return Response('No hay productos disponibles', status=404)
		
		serializer = []
		for producto in productos:
			serializer.append({
				'id': producto.id,
				'nombre': producto.nombre,
				'descripcion': producto.descripcion,
				'precio': str(producto.precio),
				'tiempoPreparacion': producto.tiempoPreparacion,
				'imagen': producto.imagen,
				'categoria': producto.categoria.nombreCategoria if producto.categoria else None,
				'mostrarEnListado': producto.mostrarEnListado,
			})
		return Response(serializer, status=200)

class BuscarProductoMenu(APIView):
	def get(self, request):

		nombre = request.data.get('nombre', '')
		if not nombre:
			return Response('El nombre del producto es obligatorio', status=400)

		productos = (
			productoMenu.objects
			.select_related('categoria')
			.filter(status=True)
			.filter(nombre__icontains=nombre)  # Solo busca en el nombre
			.order_by('nombre')
		)

		if not productos.exists():
			return Response('Producto no encontrado', status=404)

		serializer = [{
			'id': p.id,
			'nombre': p.nombre,
			'descripcion': p.descripcion,
			'precio': str(p.precio),
			'tiempoPreparacion': p.tiempoPreparacion,
			'imagen': p.imagen,
			'categoria': p.categoria.nombreCategoria if p.categoria else None,
		} for p in productos]

		return Response(serializer, status=200)