from django.db import models
from mesas.models import Mesa
from menu.models import productoMenu
from ordenes.manager import procesoPedido
from .catalogo import STATUS_CHOICES

class Pedido(models.Model):
    id = models.AutoField(primary_key=True)
    nombreOrden = models.CharField(max_length=100)  
    idMesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proceso')

    objects = procesoPedido()
    
    def __str__(self):
        return f'Pedido {self.id} - {self.nombreOrden} - Mesa {self.idMesa.numeroMesa} - {self.status}'

class DetallePedido(models.Model):
    id = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(productoMenu, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    observaciones = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proceso')
    
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre if self.producto else "Producto eliminado"} (Pedido {self.pedido.id})'