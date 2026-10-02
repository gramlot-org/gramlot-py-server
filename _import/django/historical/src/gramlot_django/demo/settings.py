# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = 'gramlot-polls-local-demo-only'
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
ROOT_URLCONF = 'gramlot_django.demo.urls'
INSTALLED_APPS = ['gramlot_django.demo.apps.PollsConfig']
MIDDLEWARE = ['django.middleware.csrf.CsrfViewMiddleware']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': Path(os.environ['GRAMLOT_POLLS_DATA_DIR']) / 'polls.sqlite3'}}
USE_TZ = True

TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True}]
