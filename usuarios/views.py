
from rest_framework.views import APIView
from rest_framework.response import Response

from usuarios.models import Usuario


class CrearUsuario(APIView):
    def post(self, request):
        nombre = request.data.get('nombre')
        email = request.data.get('email')
        password = request.data.get('password')
        isAdmin = request.data.get('isAdmin', False)

        if not nombre or not password:
            return Response({'error': 'nombre, email y password son obligatorios'}, status=400)

        if Usuario.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado'}, status=400)

        usuario = Usuario.objects.create(
            nombre=nombre,
            email=email,
            password=password,
            isAdmin=isAdmin
        )

        return Response({
            'id': usuario.id,
            'nombre': usuario.nombre,
            'email': usuario.email,
            'isAdmin': usuario.isAdmin,
        }, status=201)
          
class ModificarUsuario(APIView):
    def put(self, request):
        email = request.data.get('email')
        nombre = request.data.get('nombre')
        password = request.data.get('password')
        isAdmin = request.data.get('isAdmin')

        if not email:
            return Response({'error': 'El email es obligatorio para modificar el usuario'}, status=400)

        usuario = Usuario.objects.filter(email=email).first()
        if not usuario:
            return Response({'error': 'Usuario no encontrado'}, status=404)

        if nombre is not None:
            usuario.nombre = nombre
        if password is not None:
            usuario.password = password
        if isAdmin is not None:
            usuario.isAdmin = isAdmin

        usuario.save()

        return Response({
            'id': usuario.id,
            'nombre': usuario.nombre,
            'email': usuario.email,
            'isAdmin': usuario.isAdmin,
        }, status=200)
        
class EliminarUsuario(APIView):
    def delete(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'El email es obligatorio para eliminar el usuario'}, status=400)

        usuario = Usuario.objects.filter(email=email).first()
        if not usuario:
            return Response({'error': 'Usuario no encontrado'}, status=404)

        usuario.delete()

        return Response({'mensaje': 'Usuario eliminado correctamente'}, status=200)
    
class ListarUsuarios(APIView):
    def get(self, request):
        usuarios = Usuario.objects.all()
        lista = []
        for usuario in usuarios:
            lista.append({
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'isAdmin': usuario.isAdmin,
            })
        return Response(lista, status=200)
    
class LoginUsuario(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'El email y la contraseña son obligatorios'}, status=400)

        usuario = Usuario.objects.filter(email=email, password=password).first()
        if not usuario:
            return Response({'error': 'Credenciales incorrectas'}, status=401)

        return Response({
            'email': usuario.email,
            'isAdmin': usuario.isAdmin,
        }, status=200)
        
class HacerAdmin(APIView):
    def patch(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'El email es obligatorio'}, status=400)

        usuario = Usuario.objects.filter(email=email).first()
        if not usuario:
            return Response({'error': 'Usuario no encontrado'}, status=404)

        usuario.isAdmin = True
        usuario.save()

        return Response({
            'id': usuario.id,
            'email': usuario.email,
            'isAdmin': usuario.isAdmin,
        }, status=200)