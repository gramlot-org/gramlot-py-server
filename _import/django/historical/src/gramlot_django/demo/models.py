# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200, unique=True)
    pub_date = models.DateTimeField()


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['question', 'choice_text'],
                                               name='gramlot_polls_unique_choice')]
