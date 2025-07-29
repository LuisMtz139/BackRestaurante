
from django.db import models

from usuarios.manager import procesoUsuario


class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    isAdmin = models.BooleanField(default=False, blank=True, null=True)
    
    objects = procesoUsuario()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'