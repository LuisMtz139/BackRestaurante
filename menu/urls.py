from django.urls import path
from .views import *


urlpatterns = [
    
    #Crear categorias
    path('crearCategoriaMenu/', CrearCategoriaMenu.as_view(), name='CrearCategoriaMenu'),
    path('modificarCategoriaMenu/<int:id>/', modificarCategoriaMenu.as_view(), name='modificarCategoriaMenu'),
    path('listarCategorias/', listarCategorias.as_view(), name='listarCategorias'),
    path('eliminarCategoriaMenu/<int:id>/', eliminarCategoriaMenu.as_view(), name='eliminarCategoriaMenu'),


    #MENU
    path('crearMenu/', CrearMenu.as_view(), name='CrearMenu'),
    path('eliminarMenu/<int:id>/', eliminarMenu.as_view(), name='EliminarMenu'),
    path('modificarMenu/<int:id>/', modificarMenu.as_view(), name='ModificarMenu'),
    path('listarMenuPorCategoria/<int:categoriaId>/', listarMenuPorCategoria.as_view(), name='listarMenuPorCategoria'),
    path('listarTodoMenu/', listarTodoMenu.as_view(), name='listarTodoMenu'),
    #path('listarMenu/', listarMenu.as_view(), name='listarMenu'),

]