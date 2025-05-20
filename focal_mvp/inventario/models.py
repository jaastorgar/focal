from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    categoria = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Empresa(models.Model):
    nombre_almacen = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    direccion_tributaria = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    run_representante = models.CharField(max_length=12)
    inicio_actividades = models.DateField()
    nivel_venta_uf = models.CharField(max_length=100, blank=True)
    giro_negocio = models.CharField(max_length=100)
    tipo_sociedad = models.CharField(max_length=100)

class Almacenero(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=25)
    snombre = models.CharField(max_length=25)
    apellido = models.CharField(max_length=25)
    sapellido = models.CharField(max_length=25)
    run = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"