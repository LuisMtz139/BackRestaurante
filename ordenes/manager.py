from django.db import models
from django.conf import settings
from django.db import connection


class procesoPedido(models.Manager):
    
    def obtenerPedidoEnProceso(self):
        return self.filter(status='proceso').order_by('fecha')


