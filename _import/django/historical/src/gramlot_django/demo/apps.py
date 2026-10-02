# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.apps import AppConfig


class PollsConfig(AppConfig):
    name = 'gramlot_django.demo'
    label = 'gramlot_polls'
    default_auto_field = 'django.db.models.BigAutoField'
