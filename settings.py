from decouple import config

SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG      = config("DEBUG", default=False, cast=bool)

