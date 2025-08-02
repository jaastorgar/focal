from django.contrib.auth.models import BaseUserManager
from django.db import transaction

class AlmaceneroManager(BaseUserManager):
    """
    Manager personalizado para el modelo Almacenero.
    """
    def _create_user(self, email, password, **extra_fields):
        """
        Crea y guarda un usuario con email y contraseña.
        """
        if not email:
            raise ValueError('El campo Email es obligatorio.')

        with transaction.atomic():
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self._create_user(email, password, **extra_fields)