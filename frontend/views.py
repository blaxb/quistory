# frontend/views.py  (only the quiz_view function changed)

import os
import json
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from requests.exceptions import RequestException
from .forms import LoginForm, RegisterForm, TopicForm

DJANGO_API_BASE = os.environ.get("DJANGO_API_BASE", "http://127.0.0.1:8000")
QUIZ_API_BASE   = f"{DJANGO_API_BASE}/api/quiz"


def quiz_view(request):
    form = TopicForm(request.POST or None)
    quiz = None

    if form.is_valid():
        topic = form.cleaned_data["topic"]
        try:
            resp = requests.post(
                f"{QUIZ_API_BASE}/generate-quiz/",
                json={"topic": topic},
                timeout=15,
            )
            # --- DEBUG: log what we sent & what we got ---
            print(f"[quiz_view] POST -> {QUIZ_API_BASE}/generate-quiz/ topic={topic!r} "
                  f"status={resp.status_code}")
            print(f"[quiz_view] Response body (first 500 chars): {resp.text[:500]}")
            resp.raise_for_status()
        except RequestException as e:
            messages.error(request, f"Couldn’t generate quiz: {e}")
        else:
            # Defensive normalization so the template JS never crashes
            try:
                data = resp.json()
            except ValueError:
                data = None
            if isinstance(data, dict):
                # ensure quiz_type is present
                if "quiz_type" not in data:
                    data["quiz_type"] = "list"
                # ensure items is a list
                if not isinstance(data.get("items"), list):
                    data["items"] = []
                quiz = data
            elif isinstance(data, list):
                # if an API ever returns a raw list, wrap it
                quiz = {"quiz_type": "list", "topic": topic, "items": data}
            else:
                quiz = {"quiz_type": "list", "topic": topic, "items": []}
                messages.error(request, "Quiz service returned an unexpected format.")

    return render(request, "frontend/quiz.html", {"form": form, "quiz": quiz})

