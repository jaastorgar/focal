from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import AlmaceneroManager
from django.conf import settings

# --- TUS LISTAS DE OPCIONES ---
COMUNA_CHOICES = [
    ('Seleccione la comuna', 'Seleccione la comuna'), 
    ('Alhué', 'Alhué'), 
    ('Buín', 'Buín'), 
    ('Calera de Tango', 'Calera de Tango'), 
    ('Cerrillos', 'Cerrillos'), 
    ('Cerro Navia', 'Cerro Navia'), 
    ('Colina', 'Colina'), 
    ('Conchalí', 'Conchalí'), 
    ('Curacaví', 'Curacaví'), 
    ('El Bosque', 'El Bosque'), 
    ('El Monte', 'El Monte'), 
    ('Estación Central', 'Estación Central'), 
    ('Huechuraba', 'Huechuraba'), 
    ('Independencia', 'Independencia'), 
    ('Isla de Maipo', 'Isla de Maipo'), 
    ('La Cisterna', 'La Cisterna'), 
    ('La Florida', 'La Florida'), 
    ('La Granja', 'La Granja'), 
    ('La Pintana', 'La Pintana'), 
    ('La Reina', 'La Reina'), 
    ('Lampa', 'Lampa'), 
    ('Las Condes', 'Las Condes'), 
    ('Lo Barnechea', 'Lo Barnechea'), 
    ('Lo Espejo', 'Lo Espejo'), 
    ('Lo Prado', 'Lo Prado'), 
    ('Macul', 'Macul'), 
    ('Maipú', 'Maipú'), 
    ('María Pinto', 'María Pinto'), 
    ('Melipilla', 'Melipilla'), 
    ('Ñuñoa', 'Ñuñoa'), 
    ('Padre Hurtado', 'Padre Hurtado'), 
    ('Paine', 'Paine'), 
    ('Pedro Aguirre Cerda', 'Pedro Aguirre Cerda'), 
    ('Peñalolén', 'Peñalolén'), 
    ('Peñaflor', 'Peñaflor'), 
    ('Pirque', 'Pirque'), 
    ('Providencia', 'Providencia'), 
    ('Pudahuel', 'Pudahuel'), 
    ('Puente Alto', 'Puente Alto'), 
    ('Quilicura', 'Quilicura'), 
    ('Quinta Normal', 'Quinta Normal'), 
    ('Recoleta', 'Recoleta'), 
    ('Renca', 'Renca'), 
    ('San Bernardo', 'San Bernardo'), 
    ('San Joaquín', 'San Joaquín'), 
    ('San José de Maipo', 'San José de Maipo'), 
    ('San Miguel', 'San Miguel'), 
    ('San Pedro', 'San Pedro'), 
    ('San Ramón', 'San Ramón'), 
    ('Santiago', 'Santiago'), 
    ('Talagante', 'Talagante'), 
    ('Til Til', 'Til Til'), 
    ('Vitacura', 'Vitacura'),
]

UNIDAD_MEDIDA_CHOICES = [
    ('un', 'Unidad'), 
    ('kg', 'Kilogramo'), 
    ('g', 'Gramo'), 
    ('l', 'Litro'), 
    ('ml', 'Mililitro')
]

CATEGORIA_CHOICES = [
    ('abarrotes', 'Abarrotes'), 
    ('frutas_verduras', 'Frutas y Verduras'), 
    ('carniceria', 'Carnicería'), 
    ('panaderia', 'Panadería'), 
    ('lacteos_huevos', 'Lácteos y Huevos')
]

# --- MODELO DE USUARIO PRINCIPAL ---
class Almacenero(AbstractUser):
    username = None
    email = models.EmailField('correo electrónico', unique=True)
    nombre = models.CharField(max_length=25, blank=True)
    snombre = models.CharField(max_length=25, blank=True)
    apellido = models.CharField(max_length=25, blank=True)
    sapellido = models.CharField(max_length=25, blank=True)
    run = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, choices=COMUNA_CHOICES, default='Seleccione la comuna', blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='almaceneros'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'run']

    objects = AlmaceneroManager()

    def __str__(self):
        return self.email

class Empresa(models.Model):
    nombre_almacen = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    direccion_tributaria = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, choices=COMUNA_CHOICES, default='Seleccione la comuna', blank=True)
    run_representante = models.CharField(max_length=12)
    inicio_actividades = models.DateField()
    nivel_venta_uf = models.CharField(max_length=100, blank=True)
    giro_negocio = models.CharField(max_length=100)
    tipo_sociedad = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_almacen

class Producto(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES, blank=True, null=True)
    dramage = models.CharField(max_length=50, blank=True, null=True)
    unidad_medida = models.CharField(max_length=50, choices=UNIDAD_MEDIDA_CHOICES, blank=True, null=True)
    empresas = models.ManyToManyField(Empresa, through='OfertaProducto', related_name='productos_ofrecidos')
    creado = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

class OfertaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('producto', 'empresa')

    def __str__(self):
        return f"{self.producto.nombre} - {self.empresa.nombre}"

class LoteProducto(models.Model):
    producto = models.ForeignKey(OfertaProducto, on_delete=models.CASCADE, related_name='lotes')
    cantidad = models.PositiveIntegerField()
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Lote de {self.producto.producto.nombre} - Cantidad: {self.cantidad}"

class PlanSuscripcion(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    max_productos = models.IntegerField(default=0)
    max_lotes = models.IntegerField(default=0)
    max_empresas = models.IntegerField(default=1)

    def __str__(self):
        return self.nombre

class SuscripcionUsuario(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(PlanSuscripcion, on_delete=models.SET_NULL, null=True)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Suscripción de {self.empresa.nombre_almacen} al plan {self.plan.nombre}"

class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = [('ENTRADA', 'Entrada'), ('SALIDA', 'Salida')]
    lote = models.ForeignKey(LoteProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.tipo} de {self.cantidad} para {self.lote.producto.producto.nombre}"
    
class OrdenVenta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='ordenes_venta')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Venta #{self.id} - {self.empresa.nombre_almacen}"

class DetalleOrden(models.Model):
    orden = models.ForeignKey(OrdenVenta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(OfertaProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.producto.nombre} en Venta #{self.orden.id}"