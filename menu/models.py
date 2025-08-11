from django.db import models

from menu.manager import *

class CategoriaMenu(models.Model):
    id = models.AutoField(primary_key=True)
    nombreCategoria = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(default=True)
    ordenMenu = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProcesosCategoriaMenu()
    
    def __str__(self):
        return self.nombreCategoria
        


class productoMenu(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(CategoriaMenu, on_delete=models.SET_NULL, null=True)
    status = models.BooleanField(default=True)
    tiempoPreparacion = models.IntegerField(default=0, blank=True, null=True) 
    imagen = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProcesosMenu()
    
    def __str__(self):
        return self.nombre
    

    