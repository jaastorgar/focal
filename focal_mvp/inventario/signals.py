from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount.signals import social_account_added
from django.contrib import messages
from django.utils import timezone

from .models import Empresa, SuscripcionUsuario, PlanSuscripcion


def _ensure_empresa_y_plan(user):
    """
    Crea una Empresa por defecto y una Suscripción activa si faltan.
    Compatible con tu modelo actual (sin campos 'codigo' ni 'activo' en PlanSuscripcion).
    """
    # 1) Empresa
    if not getattr(user, "empresa_id", None):
        nombre_def = f"Almacén de {getattr(user, 'nombres', None) or user.first_name or user.email.split('@')[0]}"
        
        empresa = Empresa.objects.create(
            nombre_almacen=nombre_def,
            razon_social=nombre_def,
            rut=f"PEND-{user.id}",  # temporal, evita duplicados
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

    # 2) Plan: selecciona el más económico o el primero disponible
    plan = PlanSuscripcion.objects.order_by("precio").first()

    # Evita duplicados de suscripción activa
    if plan and not SuscripcionUsuario.objects.filter(empresa=empresa, activa=True).exists():
        SuscripcionUsuario.objects.create(
            empresa=empresa,
            plan=plan,
            activa=True
        )


@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    _ensure_empresa_y_plan(user)
    messages.info(request, "¡Bienvenido! Creamos tu almacén y activamos un plan inicial.")


@receiver(social_account_added)
def handle_social_added(request, sociallogin, **kwargs):
    _ensure_empresa_y_plan(sociallogin.user)


@receiver(user_logged_in)
def handle_user_logged_in(request, user, **kwargs):
    _ensure_empresa_y_plan(user)