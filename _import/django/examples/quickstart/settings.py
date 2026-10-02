# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Minimal local demonstration; configure secrets and hosts for your deployment."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'local-gramlot-quickstart-only')
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
ROOT_URLCONF = 'urls'
INSTALLED_APPS = []
MIDDLEWARE = ['django.middleware.csrf.CsrfViewMiddleware']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': BASE_DIR / 'db.sqlite3'}}
