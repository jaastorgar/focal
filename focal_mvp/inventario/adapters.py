from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class FocalAccountAdapter(DefaultAccountAdapter):
    """Adapter para registros locales (no sociales). Lo dejamos simple."""
    def is_open_for_signup(self, request):
        return True

class FocalSocialAdapter(DefaultSocialAccountAdapter):
    """
    Mapea los datos que trae Google a tu modelo de usuario (Almacenero),
    que usa campos personalizados como 'nombres' y 'apellidos' y NO username.
    """
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Google suele traer estos keys:
        first = data.get("first_name") or data.get("given_name") or ""
        last  = data.get("last_name")  or data.get("family_name") or ""
        email = data.get("email") or getattr(user, "email", "") or ""

        # Asigna a tus campos
        try:
            if hasattr(user, "nombres"):
                user.nombres = first or user.nombres
            if hasattr(user, "apellidos"):
                user.apellidos = last or user.apellidos
        except Exception:
            pass

        user.email = email or user.email
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Guarda el usuario social garantizando que no falten campos
        que tu modelo exige. Luego deja a allauth enlazar la cuenta social.
        """
        user = sociallogin.user

        # Default a email si algo viene vacío (previene IntegrityError)
        if not getattr(user, "email", None):
            extra = sociallogin.account.extra_data or {}
            user.email = extra.get("email", "")

        # Campos opcionales defensivos
        for fld in ("telefono", "direccion", "region", "comuna"):
            if hasattr(user, fld) and getattr(user, fld, None) is None:
                setattr(user, fld, "")

        user.save()  # guarda el User
        return super().save_user(request, sociallogin, form)