from rest_framework.views import APIView
from rest_framework.response import Response
from menu.manager import ProcesosMenu
from menu.models import  *
import base64
from django.db.models import Sum, Q, F
from datetime import datetime
from ordenes.models import *


#categoriaMetricas
class ListarCategoriaMetricas(APIView):
	def get(self, request):
		categorias = categoriaMetricas.objects.filter(status=True).order_by('id')
		
		if not categorias.exists():
			return Response({'error': 'No hay categorías métricas configuradas'}, status=400)
		
		response_data = []
		for cat_metrica in categorias:
			response_data.append({
				'id': cat_metrica.id,
				'nombreCategoria': cat_metrica.nombreCategoria
			})
		
		return Response(response_data, status=200)

class CrearCategoriaMetricas(APIView):
    def post(self, request):
        nombreCategoria = request.data['nombreCategoria']
        
        if not nombreCategoria:
            return Response('Nombre no asigando')
        
        categoria = categoriaMetricas.objects.create( nombreCategoria=nombreCategoria)
	
        return Response({
            'id': categoria.id,
            'nombreCategoria': categoria.nombreCategoria,
        }, status=201)
        
class ModificarCategoriaMetricas(APIView):
	def put(self, request, id):
		nombreCategoria = request.data.get('nombreCategoria')
		if not nombreCategoria:
			return Response('Nombre no asigando')
		
		categoria = categoriaMetricas.objects.filter(id=id).first()
		if not categoria:
			return Response('Categoría no encontrada')
		
		categoria.nombreCategoria = nombreCategoria
		categoria.save()
		
		return Response({
			'id': categoria.id,
			'nombreCategoria': categoria.nombreCategoria,
		}, status=200)
  
class EliminarCategoriaMetricas(APIView):
	def delete(self, request, id):
		if not id:
			return Response({'error': 'El ID es obligatorio'}, status=400)
		
		categoria = categoriaMetricas.objects.filter(id=id).first()
		if not categoria:
			return Response({'error': 'Categoría no encontrada'}, status=404)

		categoria.delete()
		return Response({'mensaje': 'Categoría eliminada correctamente'}, status=200)

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
		fecha = request.GET.get('fecha')
		if not fecha:
			return Response({'error': 'El parámetro fecha es requerido (formato: YYYY-MM-DD)'}, status=400)
		
		try:
			fecha_parsed = datetime.strptime(fecha, '%Y-%m-%d').date()
		except ValueError:
			return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)
		
		# Filtro para UN DÍA ESPECÍFICO únicamente
		detalles_base = DetallePedido.objects.filter( pedido__fecha__date=fecha_parsed, pedido__status='completado', status='pagado' )
		
		# Obtener todas las categorías métricas activas
		categorias_metricas = categoriaMetricas.objects.filter(status=True).order_by('id')
		
		if not categorias_metricas.exists():
			return Response({'error': 'No hay categorías métricas configuradas'}, status=400)
		
		# Preparar respuesta dinámica
		response_data = {}
		total_general = 0
		cantidad_general = 0
		
		# Calcular totales para cada categoría métrica
		for cat_metrica in categorias_metricas:
			queryset = detalles_base.filter( producto__categoriaMetrica_id=cat_metrica.id )
			
			datos = queryset.aggregate( total=Sum(F('cantidad') * F('producto__precio')), cantidad=Sum('cantidad') )
			
			total = datos['total'] or 0
			cantidad = datos['cantidad'] or 0

			nombre = cat_metrica.nombreCategoria
			
			# Convertir a camelCase
			palabras = nombre.split()
			if len(palabras) > 1:
				clave = palabras[0].lower() + ''.join(word.capitalize() for word in palabras[1:])
			else:
				clave = palabras[0].lower()
			
			# Remover acentos
			clave = (clave
				.replace('á', 'a').replace('é', 'e').replace('í', 'i')
				.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
				.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
				.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
			)
			
			response_data[clave] = {
				'total': float(total),
				'cantidad': cantidad,
				'categoria_id': cat_metrica.id,
				'categoria_nombre': cat_metrica.nombreCategoria
			}
			
			total_general += total
			cantidad_general += cantidad
		
		# Agregar total general
		response_data['totalGeneral'] = {
			'total': float(total_general),
			'cantidad': cantidad_general
		}
		
		return Response(response_data, status=200)	
		
# Menu
class CrearMenu(APIView):
	def post(self, request):
		nombre = request.POST.get('nombre')
		descripcion = request.POST.get('descripcion')
		precio = request.POST.get('precio')
		tiempoPreparacion = request.POST.get('tiempoPreparacion')
		categoriaId = request.POST.get('categoriaId')
		idCategoriasMetricas = request.POST.get('idCategoriasMetricas')

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

		obtenerCategoriaMetrica = categoriaMetricas.objects.filter(id=idCategoriasMetricas).first()
		if not obtenerCategoriaMetrica:
			return Response('Categoría métrica no encontrada', status=404)
		
		producto = productoMenu.objects.create(
			nombre=nombre,
			descripcion=descripcion,
			precio=precio,
			tiempoPreparacion=tiempoPreparacion,
			imagen=imagen,
			categoria=categoria,
			categoriaMetrica = obtenerCategoriaMetrica
		)

		return Response({
			'id': producto.id,
			'nombre': producto.nombre,
			'descripcion': producto.descripcion,
			'precio': str(producto.precio),
			'tiempoPreparacion': producto.tiempoPreparacion,
			'imagen': producto.imagen,
			'categoria': producto.categoria.nombreCategoria if producto.categoria else None,
			'categoriaMetrica': producto.categoriaMetrica.nombreCategoria if producto.categoriaMetrica else None,
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
		categoriaMetrica = request.POST.get('idCategoriasMetricas')	

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

		if categoriaMetrica:
			obtenerCategoriaMetrica = categoriaMetricas.objects.filter(id=categoriaMetrica).first()
			producto.categoriaMetrica = obtenerCategoriaMetrica
   
		producto.save()

		return Response({
			'id': producto.id,
			'nombre': producto.nombre,
			'descripcion': producto.descripcion,
			'precio': str(producto.precio),
			'tiempoPreparacion': producto.tiempoPreparacion,
			'imagen': producto.imagen,
			'categoria': producto.categoria.id if producto.categoria else None,
			'categoriaMetrica': categoriaMetrica
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
				'categoriaMetricaNombre': producto.categoriaMetrica.nombreCategoria if producto.categoriaMetrica else None,
				'categoriaMetricaId': producto.categoriaMetrica.id if producto.categoriaMetrica else None,
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