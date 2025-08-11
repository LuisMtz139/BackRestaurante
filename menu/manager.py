from django.db import models
from django.conf import settings
from django.db import connection

class ProcesosCategoriaMenu(models.Manager):

    def obtenerExistenciaCategoria(self, nombreCategoria):
        categoria = self.filter(nombreCategoria=nombreCategoria).first()
        if not categoria:
            return None
        return categoria

    def verificarExistenciaCategoria(self, nombreCategoria, descripcion):
        
        categoria = self.filter(nombreCategoria=nombreCategoria).first()
        if not categoria:
            return None
        return categoria
    
    def verificarExistenciaCategoriaPorId(self, id):
        
        categoria = self.filter(id=id).first()
        if not categoria:
            return None
        return categoria
    
    def obtenerCategorias(self):
        categorias = self.all().filter(status=True).order_by('ordenMenu')
        if not categorias:
            return None
        return categorias
    
    def validarExistenciaCategoria(self, id):
        categoria = self.filter(id=id).first()
        if not categoria:
            return None
        return categoria

    

    
    
class ProcesosMenu(models.Manager):
    
    def eliminarMenu(self, id):
        menu = self.filter(id=id).first()
        if not menu:
            return None
        menu.delete()
        return True
    
    def obtenerMenuPorCategoria(self, categoria_id):
        return self.filter(categoria=categoria_id, status=True)
    
    def listarTodoMenu(self):
        return self.filter(status=True)
    