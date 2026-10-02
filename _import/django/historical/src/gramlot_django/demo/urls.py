# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView
from gramlot_django import DjangoPageCollection
from . import views

pages = DjangoPageCollection(settings.BASE_DIR, prefix='/polls/spa', title='Polls workspace',
                             template_name='polls/spa.html')
urlpatterns = [
    path('', RedirectView.as_view(url='/polls/', permanent=False)),
    path('polls/', views.index, name='polls-index'),
    path('polls/spa/', include(pages.urls)),
    path('polls/<int:question_id>/', views.detail, name='polls-detail'),
    path('polls/<int:question_id>/vote/', views.vote, name='polls-vote'),
    path('polls/<int:question_id>/results/', views.results, name='polls-results'),
    path('ui/polls/', RedirectView.as_view(url='/polls/', permanent=False)),
]
