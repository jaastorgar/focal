# test_email.py

import os
import django

# Establece las variables de entorno y configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "focal_project.settings")
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Probando envío de correo desde:", settings.EMAIL_HOST_USER)

try:
    send_mail(
        'Correo de prueba desde Django (test_email.py)',
        'Hola Barto, esto es una prueba automática desde el script externo.',
        settings.DEFAULT_FROM_EMAIL,
        ['javi_roman@live.com'],
        fail_silently=False,
    )
    print("✅ Correo enviado correctamente.")
except Exception as e:
    print("❌ Error al enviar el correo:")
    print(e)