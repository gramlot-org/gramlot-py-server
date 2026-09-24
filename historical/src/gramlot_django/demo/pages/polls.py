# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from uuid import uuid4
from django.db.models import F
from django.utils import timezone
from gramlot.page import endpoint, source
from gramlot_django import DjangoPage
from gramlot_django.demo.models import Choice, Question


class Page(DjangoPage):
    title = 'Polls'

    def main(self, root):
        root.h1('Interactive polls')
        root.p('A Gramlot SPA inside the Polls site, using the same questions and votes.')
        root.p('Choose an answer to vote. This local demo allows repeat votes.')
        for question in Question.objects.filter(pub_date__lte=timezone.now()).order_by('id'):
            panel = root.contentPane(style='margin: 20px 0; padding: 16px; border: 1px solid #ddd;')
            panel.h2(question.question_text)
            receipt = f'receipt_{question.pk}'
            root.data(receipt, '')
            for choice in question.choices.order_by('id'):
                event = f'vote_{choice.pk}'
                panel.button(choice.choice_text, fire=event)
                panel.dataRpc(receipt, self.vote, choice_id=choice.pk, _fired=f'^{event}',
                              _onError='this.SET("error", error.message);')
            panel.contentPane().remote(self.results, question_id=question.pk,
                                       revision=f'^{receipt}')
        root.p('^error', role='alert')

    @endpoint
    def vote(self, choice_id: int):
        updated = Choice.objects.filter(
            pk=choice_id, question__pub_date__lte=timezone.now(),
        ).update(votes=F('votes') + 1)
        if not updated:
            raise ValueError('This choice is not available')
        return uuid4().hex

    @source
    def results(self, root, question_id: int, revision: str = ''):
        root.h3('Results')
        for choice in Choice.objects.filter(
                question_id=question_id, question__pub_date__lte=timezone.now()).order_by('id'):
            root.p(f'{choice.choice_text}: {choice.votes}', id=f'result-{choice.pk}')
