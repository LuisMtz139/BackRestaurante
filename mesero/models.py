from django.db import models

class Mesero(models.Model):
	nombre = models.CharField(max_length=100)
	status = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)


	def __str__(self):
		return self.nombre