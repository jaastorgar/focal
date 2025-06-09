import os
import sys

# Agrega el directorio del proyecto
sys.path.insert(0, os.path.dirname(__file__))

# Nombre del módulo settings de tu proyecto
os.environ['DJANGO_SETTINGS_MODULE'] = 'focal_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()