#!/usr/bin/env python
"""Run the local invoice demonstration."""
import os
import sys
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_site.settings')
execute_from_command_line(sys.argv)
