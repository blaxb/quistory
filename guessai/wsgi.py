import os
from django.core.wsgi import get_wsgi_application

# ← point to guessai.settings, not "settings"!
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guessai.settings")

application = get_wsgi_application()

