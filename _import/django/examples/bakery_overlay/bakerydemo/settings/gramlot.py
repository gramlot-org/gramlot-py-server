"""Local Gramlot integration; uses only the copied SQLite database."""
from pathlib import Path

from django.conf import global_settings
from .test import *  # noqa: F403
from .test import TEMPLATES as TEMPLATES

DEBUG = True
ROOT_URLCONF = 'bakerydemo.gramlot_urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': str(Path(__file__).resolve().parents[2] / 'bakerydemodb')}}
# Resolve host templates independently of the directory used to launch manage.py.
TEMPLATES[0]['DIRS'] = [str(Path(__file__).resolve().parents[1] / 'templates')]

# Use normal password verification for the copied PBKDF2 demo accounts.
PASSWORD_HASHERS = global_settings.PASSWORD_HASHERS
