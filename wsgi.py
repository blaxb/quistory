import os
from django.core.wsgi import get_wsgi_application

# If your settings live in settings.py at root:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Or if you use production.py for prod settings, uncomment:
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "production")

application = get_wsgi_application()

