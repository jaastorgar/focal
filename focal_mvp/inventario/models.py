from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date
from django.db.models import Q

# ===========================
# DEFINICIÓN DE REGIONES Y COMUNAS POR REGIÓN
# ===========================
REGIONES_COMUNAS = {
    'Arica y Parinacota': [
        ('Arica', 'Arica'),
        ('Camarones', 'Camarones'),
        ('Putre', 'Putre'),
        ('General Lagos', 'General Lagos'),
    ],
    'Tarapacá': [
        ('Iquique', 'Iquique'),
        ('Alto Hospicio', 'Alto Hospicio'),
        ('Pozo Almonte', 'Pozo Almonte'),
        ('Camiña', 'Camiña'),
        ('Colchane', 'Colchane'),
        ('Huara', 'Huara'),
        ('Pica', 'Pica'),
    ],
    'Antofagasta': [
        ('Antofagasta', 'Antofagasta'),
        ('Mejillones', 'Mejillones'),
        ('Sierra Gorda', 'Sierra Gorda'),
        ('Taltal', 'Taltal'),
        ('Calama', 'Calama'),
        ('Ollagüe', 'Ollagüe'),
        ('San Pedro de Atacama', 'San Pedro de Atacama'),
        ('Tocopilla', 'Tocopilla'),
        ('María Elena', 'María Elena'),
    ],
    'Atacama': [
        ('Copiapó', 'Copiapó'),
        ('Caldera', 'Caldera'),
        ('Tierra Amarilla', 'Tierra Amarilla'),
        ('Chañaral', 'Chañaral'),
        ('Diego de Almagro', 'Diego de Almagro'),
        ('Vallenar', 'Vallenar'),
        ('Alto del Carmen', 'Alto del Carmen'),
        ('Freirina', 'Freirina'),
        ('Huasco', 'Huasco'),
    ],
    'Coquimbo': [
        ('La Serena', 'La Serena'),
        ('Coquimbo', 'Coquimbo'),
        ('Andacollo', 'Andacollo'),
        ('La Higuera', 'La Higuera'),
        ('Paiguano', 'Paiguano'),
        ('Vicuña', 'Vicuña'),
        ('Illapel', 'Illapel'),
        ('Canela', 'Canela'),
        ('Los Vilos', 'Los Vilos'),
        ('Salamanca', 'Salamanca'),
        ('Ovalle', 'Ovalle'),
        ('Combarbalá', 'Combarbalá'),
        ('Monte Patria', 'Monte Patria'),
        ('Punitaqui', 'Punitaqui'),
        ('Río Hurtado', 'Río Hurtado'),
    ],
    'Valparaíso': [
        ('Valparaíso', 'Valparaíso'),
        ('Casablanca', 'Casablanca'),
        ('Concón', 'Concón'),
        ('Juan Fernández', 'Juan Fernández'),
        ('Puchuncaví', 'Puchuncaví'),
        ('Quintero', 'Quintero'),
        ('Viña del Mar', 'Viña del Mar'),
        ('Isla de Pascua', 'Isla de Pascua'),
        ('Los Andes', 'Los Andes'),
        ('Calle Larga', 'Calle Larga'),
        ('Rinconada', 'Rinconada'),
        ('San Esteban', 'San Esteban'),
        ('La Ligua', 'La Ligua'),
        ('Cabildo', 'Cabildo'),
        ('Papudo', 'Papudo'),
        ('Petorca', 'Petorca'),
        ('Zapallar', 'Zapallar'),
        ('Quillota', 'Quillota'),
        ('Calera', 'Calera'),
        ('Hijuelas', 'Hijuelas'),
        ('La Cruz', 'La Cruz'),
        ('Nogales', 'Nogales'),
        ('San Antonio', 'San Antonio'),
        ('Algarrobo', 'Algarrobo'),
        ('Cartagena', 'Cartagena'),
        ('El Quisco', 'El Quisco'),
        ('El Tabo', 'El Tabo'),
        ('Santo Domingo', 'Santo Domingo'),
        ('San Felipe', 'San Felipe'),
        ('Catemu', 'Catemu'),
        ('Llaillay', 'Llaillay'),
        ('Panquehue', 'Panquehue'),
        ('Putaendo', 'Putaendo'),
        ('Santa María', 'Santa María'),
    ],
    'Metropolitana': [
        ('Santiago', 'Santiago'),
        ('Cerrillos', 'Cerrillos'),
        ('Cerro Navia', 'Cerro Navia'),
        ('Conchalí', 'Conchalí'),
        ('El Bosque', 'El Bosque'),
        ('Estación Central', 'Estación Central'),
        ('Huechuraba', 'Huechuraba'),
        ('Independencia', 'Independencia'),
        ('La Cisterna', 'La Cisterna'),
        ('La Florida', 'La Florida'),
        ('La Granja', 'La Granja'),
        ('La Pintana', 'La Pintana'),
        ('La Reina', 'La Reina'),
        ('Las Condes', 'Las Condes'),
        ('Lo Barnechea', 'Lo Barnechea'),
        ('Lo Espejo', 'Lo Espejo'),
        ('Lo Prado', 'Lo Prado'),
        ('Macul', 'Macul'),
        ('Maipú', 'Maipú'),
        ('Ñuñoa', 'Ñuñoa'),
        ('Pedro Aguirre Cerda', 'Pedro Aguirre Cerda'),
        ('Peñalolén', 'Peñalolén'),
        ('Providencia', 'Providencia'),
        ('Pudahuel', 'Pudahuel'),
        ('Quilicura', 'Quilicura'),
        ('Quinta Normal', 'Quinta Normal'),
        ('Recoleta', 'Recoleta'),
        ('Renca', 'Renca'),
        ('San Miguel', 'San Miguel'),
        ('San Joaquín', 'San Joaquín'),
        ('San Ramón', 'San Ramón'),
        ('Vitacura', 'Vitacura'),
        ('Puente Alto', 'Puente Alto'),
        ('Pirque', 'Pirque'),
        ('San José de Maipo', 'San José de Maipo'),
        ('Colina', 'Colina'),
        ('Lampa', 'Lampa'),
        ('Til Til', 'Til Til'),
        ('San Bernardo', 'San Bernardo'),
        ('Buin', 'Buin'),
        ('Calera de Tango', 'Calera de Tango'),
        ('Paine', 'Paine'),
        ('Melipilla', 'Melipilla'),
        ('Alhué', 'Alhué'),
        ('Curacaví', 'Curacaví'),
        ('María Pinto', 'María Pinto'),
        ('San Pedro', 'San Pedro'),
        ('Talagante', 'Talagante'),
        ('El Monte', 'El Monte'),
        ('Isla de Maipo', 'Isla de Maipo'),
        ('Padre Hurtado', 'Padre Hurtado'),
        ('Peñaflor', 'Peñaflor'),
    ],
    'O’Higgins': [
        ('Rancagua', 'Rancagua'),
        ('Codegua', 'Codegua'),
        ('Coinco', 'Coinco'),
        ('Coltauco', 'Coltauco'),
        ('Doñihue', 'Doñihue'),
        ('Graneros', 'Graneros'),
        ('Las Cabras', 'Las Cabras'),
        ('Machalí', 'Machalí'),
        ('Malloa', 'Malloa'),
        ('Olivar', 'Olivar'),
        ('Peumo', 'Peumo'),
        ('Pichidegua', 'Pichidegua'),
        ('Quinta de Tilcoco', 'Quinta de Tilcoco'),
        ('Rengo', 'Rengo'),
        ('Requínoa', 'Requínoa'),
        ('San Vicente', 'San Vicente'),
        ('Pichilemu', 'Pichilemu'),
        ('La Estrella', 'La Estrella'),
        ('Litueche', 'Litueche'),
        ('Marchihue', 'Marchihue'),
        ('Navidad', 'Navidad'),
        ('Paredones', 'Paredones'),
        ('San Fernando', 'San Fernando'),
        ('Chépica', 'Chépica'),
        ('Chimbarongo', 'Chimbarongo'),
        ('Lolol', 'Lolol'),
        ('Nancagua', 'Nancagua'),
        ('Palmilla', 'Palmilla'),
        ('Peralillo', 'Peralillo'),
        ('Placilla', 'Placilla'),
        ('Pumanque', 'Pumanque'),
        ('Santa Cruz', 'Santa Cruz'),
    ],
    'Maule': [
        ('Talca', 'Talca'),
        ('Constitución', 'Constitución'),
        ('Curepto', 'Curepto'),
        ('Empedrado', 'Empedrado'),
        ('Maule', 'Maule'),
        ('Pelarco', 'Pelarco'),
        ('Pencahue', 'Pencahue'),
        ('Río Claro', 'Río Claro'),
        ('San Clemente', 'San Clemente'),
        ('San Rafael', 'San Rafael'),
        ('Cauquenes', 'Cauquenes'),
        ('Chanco', 'Chanco'),
        ('Pelluhue', 'Pelluhue'),
        ('Curicó', 'Curicó'),
        ('Hualañé', 'Hualañé'),
        ('Licantén', 'Licantén'),
        ('Molina', 'Molina'),
        ('Rauco', 'Rauco'),
        ('Romeral', 'Romeral'),
        ('Sagrada Familia', 'Sagrada Familia'),
        ('Teno', 'Teno'),
        ('Vichuquén', 'Vichuquén'),
        ('Linares', 'Linares'),
        ('Colbún', 'Colbún'),
        ('Longaví', 'Longaví'),
        ('Parral', 'Parral'),
        ('Retiro', 'Retiro'),
        ('San Javier', 'San Javier'),
        ('Villa Alegre', 'Villa Alegre'),
        ('Yerbas Buenas', 'Yerbas Buenas'),
    ],
    'Ñuble': [
        ('Chillán', 'Chillán'),
        ('Bulnes', 'Bulnes'),
        ('Cobquecura', 'Cobquecura'),
        ('Coelemu', 'Coelemu'),
        ('Coihueco', 'Coihueco'),
        ('Chillán Viejo', 'Chillán Viejo'),
        ('El Carmen', 'El Carmen'),
        ('Ninhue', 'Ninhue'),
        ('Ñiquén', 'Ñiquén'),
        ('Pemuco', 'Pemuco'),
        ('Pinto', 'Pinto'),
        ('Portezuelo', 'Portezuelo'),
        ('Quillón', 'Quillón'),
        ('Quirihue', 'Quirihue'),
        ('San Carlos', 'San Carlos'),
        ('San Fabián', 'San Fabián'),
        ('San Ignacio', 'San Ignacio'),
        ('San Nicolás', 'San Nicolás'),
        ('Treguaco', 'Treguaco'),
        ('Yungay', 'Yungay'),
    ],
    'Biobío': [
        ('Concepción', 'Concepción'),
        ('Coronel', 'Coronel'),
        ('Chiguayante', 'Chiguayante'),
        ('Florida', 'Florida'),
        ('Hualpén', 'Hualpén'),
        ('Hualqui', 'Hualqui'),
        ('Lota', 'Lota'),
        ('Penco', 'Penco'),
        ('San Pedro de la Paz', 'San Pedro de la Paz'),
        ('Santa Juana', 'Santa Juana'),
        ('Talcahuano', 'Talcahuano'),
        ('Tomé', 'Tomé'),
        ('Hualañé', 'Hualañé'),
        ('Lebu', 'Lebu'),
        ('Arauco', 'Arauco'),
        ('Cañete', 'Cañete'),
        ('Contulmo', 'Contulmo'),
        ('Curanilahue', 'Curanilahue'),
        ('Los Álamos', 'Los Álamos'),
        ('Tirúa', 'Tirúa'),
        ('Los Ángeles', 'Los Ángeles'),
        ('Antuco', 'Antuco'),
        ('Cabrero', 'Cabrero'),
        ('Laja', 'Laja'),
        ('Mulchén', 'Mulchén'),
        ('Nacimiento', 'Nacimiento'),
        ('Negrete', 'Negrete'),
        ('Quilaco', 'Quilaco'),
        ('Quilleco', 'Quilleco'),
        ('San Rosendo', 'San Rosendo'),
        ('Santa Bárbara', 'Santa Bárbara'),
        ('Tucapel', 'Tucapel'),
        ('Yumbel', 'Yumbel'),
        ('Alto Biobío', 'Alto Biobío'),
    ],
    'Araucanía': [
        ('Temuco', 'Temuco'),
        ('Carahue', 'Carahue'),
        ('Cunco', 'Cunco'),
        ('Curarrehue', 'Curarrehue'),
        ('Freire', 'Freire'),
        ('Galvarino', 'Galvarino'),
        ('Gorbea', 'Gorbea'),
        ('Lautaro', 'Lautaro'),
        ('Loncoche', 'Loncoche'),
        ('Melipeuco', 'Melipeuco'),
        ('Nueva Imperial', 'Nueva Imperial'),
        ('Padre Las Casas', 'Padre Las Casas'),
        ('Perquenco', 'Perquenco'),
        ('Pitrufquén', 'Pitrufquén'),
        ('Pucón', 'Pucón'),
        ('Saavedra', 'Saavedra'),
        ('Teodoro Schmidt', 'Teodoro Schmidt'),
        ('Toltén', 'Toltén'),
        ('Vilcún', 'Vilcún'),
        ('Villarrica', 'Villarrica'),
        ('Cholchol', 'Cholchol'),
        ('Angol', 'Angol'),
        ('Collipulli', 'Collipulli'),
        ('Curacautín', 'Curacautín'),
        ('Ercilla', 'Ercilla'),
        ('Lonquimay', 'Lonquimay'),
        ('Los Sauces', 'Los Sauces'),
        ('Lumaco', 'Lumaco'),
        ('Purén', 'Purén'),
        ('Renaico', 'Renaico'),
        ('Traiguén', 'Traiguén'),
        ('Victoria', 'Victoria'),
    ],
    'Los Ríos': [
        ('Valdivia', 'Valdivia'),
        ('Corral', 'Corral'),
        ('Lanco', 'Lanco'),
        ('Los Lagos', 'Los Lagos'),
        ('Máfil', 'Máfil'),
        ('Mariquina', 'Mariquina'),
        ('Paillaco', 'Paillaco'),
        ('Panguipulli', 'Panguipulli'),
        ('La Unión', 'La Unión'),
        ('Futrono', 'Futrono'),
        ('Lago Ranco', 'Lago Ranco'),
        ('Río Bueno', 'Río Bueno'),
    ],
    'Los Lagos': [
        ('Puerto Montt', 'Puerto Montt'),
        ('Calbuco', 'Calbuco'),
        ('Cochamó', 'Cochamó'),
        ('Fresia', 'Fresia'),
        ('Frutillar', 'Frutillar'),
        ('Llanquihue', 'Llanquihue'),
        ('Maullín', 'Maullín'),
        ('Puerto Varas', 'Puerto Varas'),
        ('Castro', 'Castro'),
        ('Ancud', 'Ancud'),
        ('Chonchi', 'Chonchi'),
        ('Curaco de Vélez', 'Curaco de Vélez'),
        ('Dalcahue', 'Dalcahue'),
        ('Puqueldón', 'Puqueldón'),
        ('Queilén', 'Queilén'),
        ('Quellón', 'Quellón'),
        ('Quemchi', 'Quemchi'),
        ('Quinchao', 'Quinchao'),
        ('Osorno', 'Osorno'),
        ('Puerto Octay', 'Puerto Octay'),
        ('Purranque', 'Purranque'),
        ('Puyehue', 'Puyehue'),
        ('Río Negro', 'Río Negro'),
        ('San Juan de la Costa', 'San Juan de la Costa'),
        ('San Pablo', 'San Pablo'),
        ('Chaitén', 'Chaitén'),
        ('Futaleufú', 'Futaleufú'),
        ('Hualaihué', 'Hualaihué'),
        ('Palena', 'Palena'),
    ],
    'Aysén': [
        ('Coyhaique', 'Coyhaique'),
        ('Lago Verde', 'Lago Verde'),
        ('Aysén', 'Aysén'),
        ('Cisnes', 'Cisnes'),
        ('Guaitecas', 'Guaitecas'),
        ('Cochrane', 'Cochrane'),
        ('O’Higgins', 'O’Higgins'),
        ('Tortel', 'Tortel'),
        ('Chile Chico', 'Chile Chico'),
        ('Río Ibáñez', 'Río Ibáñez'),
    ],
    'Magallanes': [
        ('Punta Arenas', 'Punta Arenas'),
        ('Laguna Blanca', 'Laguna Blanca'),
        ('Río Verde', 'Río Verde'),
        ('San Gregorio', 'San Gregorio'),
        ('Porvenir', 'Porvenir'),
        ('Primavera', 'Primavera'),
        ('Timaukel', 'Timaukel'),
        ('Natales', 'Natales'),
        ('Torres del Paine', 'Torres del Paine'),
    ],
}

# Lista plana para usar en campos que no requieran filtro (opcional)
COMUNA_CHOICES = [('', 'Seleccione la comuna')] + [
    (comuna, nombre) for comunas in REGIONES_COMUNAS.values() for comuna, nombre in comunas
]

# Lista de regiones para usar en campos de selección
REGION_CHOICES = [('', 'Seleccione la región')] + [(r, r) for r in REGIONES_COMUNAS.keys()]

UNIDAD_MEDIDA_CHOICES = [
    ('un', 'Unidad'),
    ('kg', 'Kilogramo'),
    ('g', 'Gramo'),
    ('l', 'Litro'),
    ('ml', 'Mililitro'),
    ('mg', 'Miligramo'),
    ('cm', 'Centímetro'),
]

CATEGORIA_CHOICES = [
    # 🛒 Abarrotes y básicos
    ('abarrotes', 'Abarrotes'),
    ('cereales_legumbres', 'Cereales y Legumbres'),
    ('aceites_vinagres', 'Aceites y Vinagres'),
    ('conservas', 'Conservas y Enlatados'),
    ('especias_condimentos', 'Especias y Condimentos'),
    ('reposteria', 'Repostería y Postres'),

    # 🥬 Frescos y perecibles
    ('frutas_verduras', 'Frutas y Verduras'),
    ('carniceria', 'Carnicería'),
    ('pollo_granel', 'Pollo al Granel'),
    ('pescados_mariscos', 'Pescados y Mariscos'),
    ('panaderia', 'Panadería'),
    ('lacteos_huevos', 'Lácteos y Huevos'),
    ('embutidos', 'Embutidos'),
    ('congelados', 'Congelados'),

    # 🥤 Bebidas y consumo inmediato
    ('bebidas', 'Bebidas'),
    ('aguas', 'Aguas y Jugos'),
    ('cervezas', 'Cervezas'),
    ('licores', 'Licores y Vinos'),
    ('snacks', 'Snacks y Dulces'),
    ('helados', 'Helados'),

    # 🧼 Limpieza y cuidado personal
    ('limpieza', 'Artículos de Limpieza'),
    ('cuidado_personal', 'Cuidado Personal'),
    ('papeleria', 'Papelería e Higiene'),

    # 🏠 Hogar y otros
    ('hogar', 'Artículos de Hogar'),
    ('mascotas', 'Productos para Mascotas'),
    ('ferreteria_basica', 'Ferretería Básica'),
    ('bazar', 'Bazar y Misceláneos'),
]

# ===========================
# MANAGER PERSONALIZADO
# ===========================
class AlmaceneroManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def normalize_email(self, email):
        """
        Normaliza el email (necesario para compatibilidad con Django)
        """
        return super().normalize_email(email)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

# ===========================
# MODELO ALMACENERO
# ===========================
class Almacenero(AbstractUser):
    username = None
    email = models.EmailField('correo electrónico', unique=True)
    nombres = models.CharField(max_length=25, blank=True)
    apellidos = models.CharField(max_length=25, blank=True)
    run = models.CharField(
        max_length=12,
        null=True, blank=True, default=None,
        db_index=True
    )
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, choices=COMUNA_CHOICES, default='', blank=True)
    region = models.CharField(max_length=100, choices=REGION_CHOICES, default='', blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='almaceneros'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = AlmaceneroManager()

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        # Normaliza: si llega '', guárdalo como None
        if self.run == '':
            self.run = None

        if self.region and not self.comuna:
            raise ValidationError({'comuna': 'Debe seleccionar una comuna de la región elegida.'})
        if self.comuna and not self.region:
            raise ValidationError({'region': 'Debe seleccionar una región primero.'})
        if self.region and self.comuna:
            comunas_validas = [c[0] for c in REGIONES_COMUNAS.get(self.region, [])]
            if self.comuna not in comunas_validas:
                raise ValidationError({'comuna': f'La comuna "{self.comuna}" no pertenece a la región "{self.region}".'})

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['run'],
                name='uniq_almacenero_run_not_null',
                condition=~Q(run__isnull=True),
            )
        ]

# ===========================
# MODELO EMPRESA
# ===========================
class Empresa(models.Model):
    nombre_almacen = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=100, blank=True)
    rut = models.CharField(max_length=12, unique=True)
    direccion_tributaria = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=100, choices=COMUNA_CHOICES, default='', blank=True)
    region = models.CharField(max_length=100, choices=REGION_CHOICES, default='', blank=True)
    run_representante = models.CharField(max_length=12)
    inicio_actividades = models.DateField()
    nivel_venta_uf = models.CharField(max_length=100, blank=True)
    giro_negocio = models.CharField(max_length=100)
    tipo_sociedad = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_almacen

    def clean(self):
        super().clean()
        if self.region and not self.comuna:
            raise ValidationError({'comuna': 'Debe seleccionar una comuna de la región elegida.'})
        if self.comuna and not self.region:
            raise ValidationError({'region': 'Debe seleccionar una región primero.'})
        if self.region and self.comuna:
            comunas_validas = [c[0] for c in REGIONES_COMUNAS.get(self.region, [])]
            if self.comuna not in comunas_validas:
                raise ValidationError({'comuna': f'La comuna "{self.comuna}" no pertenece a la región "{self.region}".'})

# ===========================
# MODELO PROVEEDOR 
# ===========================
class Proveedor(models.Model):
    """
    Modelo para representar a un proveedor de productos.
    """
    nombre = models.CharField(max_length=150, help_text="Nombre comercial del proveedor")
    razon_social = models.CharField(max_length=200, blank=True, null=True, help_text="Razón social completa")
    rut = models.CharField(max_length=12, unique=True, help_text="RUT del proveedor (e.g., 12345678-9)")
    contacto = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del contacto principal")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

# ===========================
# MODELO PRODUCTO
# ===========================
class Producto(models.Model):
    from django.core.validators import RegexValidator
    
    # Solo dígitos, hasta 30, sin espacios
    sku = models.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='El SKU debe contener solo números (sin espacios).',
                code='invalid_sku_digits'
            )
        ]
    )
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES, blank=True, null=True)
    gramaje = models.CharField(max_length=50, blank=True, null=True)
    unidad_medida = models.CharField(max_length=50, choices=UNIDAD_MEDIDA_CHOICES, blank=True, null=True)
    empresas = models.ManyToManyField(Empresa, through='OfertaProducto', related_name='productos_ofrecidos')
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# ===========================
# MODELO OFERTA PRODUCTO (ACTUALIZADO)
# ===========================
class OfertaProducto(models.Model):
    """
    Relación entre un Producto y una Empresa (inventario).
    Representa que una empresa ofrece/vende un producto específico.
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    sell_by_weight = models.BooleanField(default=False)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_step_grams = models.IntegerField(default=5)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['producto', 'empresa'],
                name='unique_producto_empresa'
            )
        ]

    def __str__(self):
        return f"{self.producto.nombre} en {self.empresa.nombre_almacen}"

    # === Propiedades dinámicas para precios ===
    @property
    def ultimo_precio_compra(self):
        """Obtiene el último precio de compra registrado en lotes"""
        ultimo_lote = self.lotes.order_by('-fecha_ingreso').first()
        return ultimo_lote.precio_compra if ultimo_lote else 0.00

    @property
    def precio_compra_promedio(self):
        """Calcula el precio de compra promedio ponderado por cantidad"""
        lotes = self.lotes.filter(cantidad__gt=0)
        if not lotes.exists():
            return 0.00
            
        total_costo = sum(lote.costo_total for lote in lotes)
        total_cantidad = sum(lote.cantidad for lote in lotes)
        
        return round(total_costo / total_cantidad, 2) if total_cantidad > 0 else 0.00

    @property
    def ultimo_precio_venta(self):
        """Obtiene el último precio de venta registrado en lotes"""
        ultimo_lote = self.lotes.order_by('-fecha_ingreso').first()
        return ultimo_lote.precio_venta if ultimo_lote else 0.00

    @property
    def precio_venta_promedio(self):
        """Calcula el precio de venta promedio ponderado por cantidad"""
        lotes = self.lotes.filter(cantidad__gt=0)
        if not lotes.exists():
            return 0.00

        total_venta = sum(lote.precio_venta * lote.cantidad for lote in lotes)
        total_cantidad = sum(lote.cantidad for lote in lotes)
        return round(total_venta / total_cantidad, 2) if total_cantidad > 0 else 0.00

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# ===========================
# MODELO LOTE PRODUCTO 
# ===========================
class LoteProducto(models.Model):
    producto = models.ForeignKey(OfertaProducto, on_delete=models.CASCADE, related_name='lotes')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    cantidad = models.PositiveIntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-fecha_ingreso']
        verbose_name = "Lote de Producto"
        verbose_name_plural = "Lotes de Productos"

    def __str__(self):
        return f"Lote de {self.producto.producto.nombre} ({self.cantidad} unidades)"

    @property
    def costo_total(self):
        return self.cantidad * self.precio_compra

    @property
    def ganancia_unitaria(self):
        return self.precio_venta - self.precio_compra

    @property
    def ganancia_total(self):
        return self.cantidad * self.ganancia_unitaria

    def clean(self):
        if self.precio_compra < 0:
            raise ValidationError({'precio_compra': 'El precio de compra no puede ser negativo.'})
        if self.precio_venta < 0:
            raise ValidationError({'precio_venta': 'El precio de venta no puede ser negativo.'})
        if self.precio_venta < self.precio_compra:
            raise ValidationError({'precio_venta': 'El precio de venta no puede ser menor al precio de compra.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# ===========================
# MODELOS EXISTENTES 
# ===========================
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
    
class Recordatorio(models.Model):
    """
    Modelo para gestionar recordatorios y obligaciones del almacenero.
    """
    TIPO_OBLIGACION_CHOICES = [
        ('fija', 'Obligación Fija'),
        ('variable', 'Obligación Variable'),
        ('acuerdo', 'Basada en Acuerdo'),
    ]
    
    PERIODICIDAD_CHOICES = [
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('bianual', 'Bianual'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='recordatorios')
    nombre = models.CharField(max_length=200, help_text="Nombre de la obligación/recordatorio")
    descripcion = models.TextField(blank=True, help_text="Descripción detallada de la obligación")
    tipo_obligacion = models.CharField(max_length=20, choices=TIPO_OBLIGACION_CHOICES, default='variable')
    periodicidad = models.CharField(max_length=20, choices=PERIODICIDAD_CHOICES, blank=True)
    dia_mes = models.PositiveIntegerField(null=True, blank=True, help_text="Día del mes (1-31)")
    mes_anio = models.PositiveIntegerField(null=True, blank=True, help_text="Mes del año (1-12)")
    fecha_primera_ejecucion = models.DateField(help_text="Primera fecha de ejecución/recordatorio")
    fecha_ultima_ejecucion = models.DateField(null=True, blank=True)
    proxima_fecha_ejecucion = models.DateField(help_text="Próxima fecha de ejecución")
    dias_anticipacion_alerta = models.PositiveIntegerField(default=5, help_text="Días antes para enviar alerta")
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Recordatorio"
        verbose_name_plural = "Recordatorios"
        ordering = ['proxima_fecha_ejecucion']
    
    def __str__(self):
        return f"{self.nombre} - {self.empresa.nombre_almacen}"
    
    def calcular_proxima_fecha(self):
        """Calcula la próxima fecha de ejecución basada en la periodicidad"""
        from dateutil.relativedelta import relativedelta
        
        if not self.fecha_primera_ejecucion:
            return None
            
        hoy = date.today()
        
        # Si ya pasó la próxima fecha, calcular la siguiente
        if self.proxima_fecha_ejecucion and self.proxima_fecha_ejecucion < hoy:
            base_fecha = self.proxima_fecha_ejecucion
        else:
            base_fecha = self.fecha_primera_ejecucion
            
        delta = None
        if self.periodicidad == 'diaria':
            delta = relativedelta(days=1)
        elif self.periodicidad == 'semanal':
            delta = relativedelta(weeks=1)
        elif self.periodicidad == 'quincenal':
            delta = relativedelta(weeks=2)
        elif self.periodicidad == 'mensual':
            delta = relativedelta(months=1)
        elif self.periodicidad == 'bimestral':
            delta = relativedelta(months=2)
        elif self.periodicidad == 'trimestral':
            delta = relativedelta(months=3)
        elif self.periodicidad == 'semestral':
            delta = relativedelta(months=6)
        elif self.periodicidad == 'anual':
            delta = relativedelta(years=1)
        elif self.periodicidad == 'bianual':
            delta = relativedelta(years=2)
            
        if delta:
            # Calcular próxima fecha
            while base_fecha <= hoy:
                base_fecha += delta
            return base_fecha
        return self.proxima_fecha_ejecucion
    
    def dias_para_vencer(self):
        """Calcula días restantes para la próxima ejecución"""
        if self.proxima_fecha_ejecucion:
            delta = self.proxima_fecha_ejecucion - date.today()
            return delta.days
        return None
    
    def estado_alerta(self):
        """Devuelve el estado de alerta del recordatorio"""
        dias_restantes = self.dias_para_vencer()
        if dias_restantes is not None:
            if dias_restantes < 0:
                return 'vencido'
            elif dias_restantes <= self.dias_anticipacion_alerta:
                return 'proxima'
        return 'normal'