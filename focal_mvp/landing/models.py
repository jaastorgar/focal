from django.db import models

class Contacto(models.Model):
    """
    Almacena los mensajes enviados desde el formulario de contacto de la landing page.
    """
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=9)
    empresa = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-fecha_envio']
        verbose_name = "Mensaje de Contacto"
        verbose_name_plural = "Mensajes de Contacto"

    def __str__(self):
        return f"Mensaje de {self.nombre_completo} ({self.email})"