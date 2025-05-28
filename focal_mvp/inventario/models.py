from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class PlanSuscripcion(models.Model):
    NOMBRE_PLANES = [
        ('FREE', 'Gratuito'),
        ('BASIC', 'Básico'),
        ('PREMIUM', 'Premium'),
    ]
    nombre = models.CharField(max_length=50, choices=NOMBRE_PLANES, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Precio mensual
    descripcion = models.TextField(blank=True)
    max_productos = models.IntegerField(default=0, help_text="Número máximo de productos. 0 para ilimitado.")
    max_almacenes = models.IntegerField(default=1, help_text="Número máximo de almacenes. 1 para gratuito.")
    soporte_prioritario = models.BooleanField(default=False)
    # Puedes añadir más campos para otras características (ej. reportes avanzados, usuarios extra, etc.)

    def __str__(self):
        return self.get_nombre_display()
    
class SuscripcionUsuario(models.Model):
    empresa = models.OneToOneField('Empresa', on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(PlanSuscripcion, on_delete=models.SET_NULL, null=True)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_fin = models.DateField(null=True, blank=True) # Para suscripciones de duración limitada o manuales
    activa = models.BooleanField(default=True)
    # Aquí podrías añadir campos para ID de transacción de pasarela de pago, etc.

    def __str__(self):
        return f"Suscripción de {self.empresa.nombre_almacen} al plan {self.plan.get_nombre_display()}"

    class Meta:
        verbose_name_plural = "Suscripciones de Usuarios"

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
    # Añade el campo para el plan de suscripción
    # Si la empresa no tiene un plan activo en SuscripcionUsuario, por defecto usará el plan gratuito.
    # Este campo no es estrictamente necesario si usas SuscripcionUsuario.activa, pero puede ser útil
    # para un acceso rápido al plan actual. Sin embargo, la lógica de SuscripcionUsuario.activa es más robusta.
    # Por ahora, nos basaremos en SuscripcionUsuario para el estado activo.

    def __str__(self):
        return self.nombre_almacen

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

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=50, blank=True)
    categoria = models.CharField(max_length=50, blank=True)
    unidad_medida = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    precio_compra = models.IntegerField(default=0)
    precio_venta = models.IntegerField(default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')

    def __str__(self):
        return f"{self.nombre} ({self.sku})"