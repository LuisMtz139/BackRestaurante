from django.db import models

from mesas.manager import *

class Mesa(models.Model):
    id = models.AutoField(primary_key=True)
    numeroMesa = models.IntegerField(unique=True)
    status = models.BooleanField(default=True)
    
    objects = procesosMesas()

    def __str__(self):
        return f'Mesa {self.numeroMesa}'