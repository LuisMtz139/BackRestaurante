from django.urls import path
from .views import *


urlpatterns = [
    path('CrearUsuario/', CrearUsuario.as_view(), name='CrearUsuario'),
    path('ModificarUsuario/', ModificarUsuario.as_view(), name='ModificarUsuario'),
    path('EliminarUsuario/', EliminarUsuario.as_view(), name='EliminarUsuario'),
    path('ListarUsuarios/', ListarUsuarios.as_view(), name='ListarUsuarios'),
    path('obtenerUsuario/', obtenerUsuario.as_view(), name='obtenerUsuario'),
    
    path('LoginUsuario/', LoginUsuario.as_view(), name='LoginUsuario'),
    path('HacerAdmin/', HacerAdmin.as_view(), name='HacerAdmin'),
]