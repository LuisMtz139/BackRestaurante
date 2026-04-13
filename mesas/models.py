from django.db import models

from mesas.manager import *

class GrupoMesas(models.Model):
	id = models.AutoField(primary_key=True)
	nombre = models.CharField(max_length=100, blank=True, null=True)
	createdAt = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.nombre if self.nombre else f'Grupo {self.id}'

class Mesa(models.Model):
	id = models.AutoField(primary_key=True)
	numeroMesa = models.IntegerField(unique=True)
	status = models.BooleanField(default=True)
	grupo = models.ForeignKey(GrupoMesas, null=True, blank=True, on_delete=models.SET_NULL, related_name='mesas')

	objects = procesosMesas()

	def __str__(self):
		return f'Mesa {self.numeroMesa}'