"""Django settings: ``django-admin runserver --settings=settings --pythonpath=.``."""

SECRET_KEY = "development-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
ROOT_URLCONF = "urls"
INSTALLED_APPS: list[str] = []
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
