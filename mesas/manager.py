from django.db import models
from django.conf import settings
from django.db import connection


class procesosMesas(models.Manager):
    def obtenerMesas(self):
        return self.filter(status=True)
    
    def verificarExistenciaMesa(self, numeroMesa):
        mesa = self.filter(numeroMesa=numeroMesa).first()
        if mesa:
            return None
        nuevaMesa = self.create(numeroMesa=numeroMesa)
        return nuevaMesa
    
    def obtenerMesaPorId(self, id):
        return self.filter(id=id).first()
    
    def obtenerMesasConPedidoAbierto(self):
        return self.filter(pedido__status='proceso').distinct()