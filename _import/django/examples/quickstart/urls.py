# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.conf import settings
from django.urls import include, path
from gramlot_django import DjangoPageCollection

pages = DjangoPageCollection(settings.BASE_DIR, prefix='/tools/ui', title='Hello Gramlot')
urlpatterns = [path('tools/ui/', include(pages.urls))]
