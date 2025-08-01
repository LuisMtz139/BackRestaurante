from django.urls import path
from .views import *


urlpatterns = [
    path('crearMesa/', CrearMesa.as_view(), name='CrearMesa'),
    path('eliminarMesa/<int:id>/', EliminarMesa.as_view(), name='EliminarMesa'),
    path('modificarStatusMesa/<int:id>/', modificarStatusMesa.as_view(), name='modificarStatusMesa'),
    path('listarMesas/', lsitarMesasStatus.as_view (), name='listarMesas'),
    path('liberarMesa/<int:mesa_id>/', LiberarMesa.as_view(), name='LiberarMesa'),
]