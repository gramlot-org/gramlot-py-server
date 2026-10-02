#!/usr/bin/env python
# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Run the minimal Django project with installed Gramlot packages."""
import os
import sys

from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
execute_from_command_line(sys.argv)
