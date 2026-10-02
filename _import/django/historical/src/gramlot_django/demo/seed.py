# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.db import transaction
from django.utils import timezone
from .models import Choice, Question


def seed():
    with transaction.atomic():
        question, _ = Question.objects.get_or_create(
            question_text='What would you like to build with Gramlot?',
            defaults={'pub_date': timezone.now()},
        )
        for text in ('A dashboard', 'A business application', 'A content editor'):
            Choice.objects.get_or_create(question=question, choice_text=text)
