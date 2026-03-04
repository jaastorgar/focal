from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import messages
from .models import Empresa, SuscripcionUsuario, PlanSuscripcion

User = get_user_model()

def _ensure_empresa_y_plan(user):
    """
    Crea una Empresa por defecto y una Suscripción activa si faltan.
    """
    if not getattr(user, "empresa_id", None):
        nombre_def = f"Almacén de {user.username}"
        
        empresa = Empresa.objects.create(
            nombre_almacen=nombre_def,
            razon_social=nombre_def,
            rut=f"PEND-{user.id}", 
            direccion_tributaria="Por definir",
            comuna="",
            region="",
            run_representante=f"RUN-{user.id}",
            inicio_actividades=timezone.now().date(),
            nivel_venta_uf="Por definir",
            giro_negocio="Almacén de barrio",
            tipo_sociedad="Persona Natural",
        )

        user.empresa = empresa
        user.save(update_fields=["empresa"])
    else:
        empresa = user.empresa

    plan = PlanSuscripcion.objects.order_by("precio").first()

    if plan and not SuscripcionUsuario.objects.filter(empresa=empresa, activa=True).exists():
        SuscripcionUsuario.objects.create(
            empresa=empresa,
            plan=plan,
            activa=True
        )

# Esta señal se dispara cada vez que se crea un usuario nuevo en Django
@receiver(post_save, sender=User)
def handle_user_created(sender, instance, created, **kwargs):
    if created:
        _ensure_empresa_y_plan(instance)