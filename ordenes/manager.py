from django.db import models
from django.conf import settings
from django.db import connection


class procesoPedido(models.Manager):
    
    def obtenerPedidoEnProceso(self):
        return self.filter(status='proceso').order_by('fecha')

    def actualizarPedido(self, id, status):
        pedido = self.filter(id=id).first()
        if not pedido:
            return None
        pedido.status = status
        pedido.save()
        return pedido