from .settings import *

DEBUG = False
ALLOWED_HOSTS = ["yourdomain.com", "www.yourdomain.com"]

# Ensure you have a secure SECRET_KEY in the environment
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# Static files (CSS, JS, images)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Optional: configure logging for errors
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

