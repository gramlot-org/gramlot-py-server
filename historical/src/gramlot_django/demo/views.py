# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .models import Question


def published():
    return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')


@require_GET
def index(request):
    return render(request, 'polls/index.html', {'questions': published()})


@require_GET
def detail(request, question_id):
    return render(request, 'polls/detail.html', {'question': get_object_or_404(published(), pk=question_id)})


@require_POST
def vote(request, question_id):
    question = get_object_or_404(published(), pk=question_id)
    try:
        choice_id = int(request.POST.get('choice', ''))
    except ValueError:
        choice_id = None
    if choice_id is None or not question.choices.filter(pk=choice_id).update(votes=F('votes') + 1):
        return render(request, 'polls/detail.html',
                      {'question': question, 'error': 'Please select an available choice.'}, status=400)
    return redirect('polls-results', question_id=question.pk)


@require_GET
def results(request, question_id):
    return render(request, 'polls/results.html', {'question': get_object_or_404(published(), pk=question_id)})
