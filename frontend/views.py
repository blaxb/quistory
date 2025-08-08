# frontend/views.py
import os
import logging
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from requests.exceptions import RequestException
from .forms import LoginForm, RegisterForm, TopicForm

# External APIs (only used for auth/leaderboard)
DJANGO_API_BASE = os.environ.get("DJANGO_API_BASE", "http://127.0.0.1:8000")
QUIZ_API_BASE   = f"{DJANGO_API_BASE}/api/quiz"

# Import the local quiz generator so the quiz page works without HTTP calls
from quiz_logic import generate_quiz as logic_generate_quiz

log = logging.getLogger("frontend")


def home(request):
    return redirect("quiz")


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        try:
            resp = requests.post(
                f"{DJANGO_API_BASE}/api/auth/register/",
                json={
                    "username":  form.cleaned_data["username"],
                    "email":     form.cleaned_data["email"],
                    "password":  form.cleaned_data["password"],
                    "password2": form.cleaned_data["password2"],
                },
                timeout=10,
            )
            resp.raise_for_status()
        except RequestException as e:
            messages.error(request, f"Registration service error: {e}")
        else:
            if resp.status_code == 201:
                messages.success(request, "Account created! Please log in.")
                return redirect("login")
            try:
                for field, errs in resp.json().items():
                    form.add_error(field, errs)
            except Exception:
                messages.error(request, "Registration failed.")
    return render(request, "frontend/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        try:
            resp = requests.post(
                f"{DJANGO_API_BASE}/api/auth/login/",
                json=form.cleaned_data,
                timeout=10,
            )
            resp.raise_for_status()
        except RequestException:
            messages.error(request, "Invalid credentials or auth service down.")
        else:
            data = resp.json()
            request.session["token"]         = data.get("access")
            request.session["refresh_token"] = data.get("refresh")
            return redirect("quiz")
    return render(request, "frontend/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    return redirect("quiz")


def quiz_view(request):
    """
    Generate the quiz by calling local Python (no HTTP).
    This avoids any DJANGO_API_BASE problems and makes the page reliable.
    """
    form = TopicForm(request.POST or None)
    quiz = None
    topic = None

    if request.method == "POST" and form.is_valid():
        topic = form.cleaned_data["topic"]
        try:
            data = logic_generate_quiz(topic)  # returns {"topic": str, "items": List[str]}
            quiz = {
                "quiz_type": "list",
                "items": data.get("items", []),
                "topic": data.get("topic", topic),
            }
            log.info("quiz_view generated %d items for topic=%r", len(quiz["items"]), topic)
        except Exception as e:
            log.exception("quiz generation error for topic=%r", topic)
            messages.error(request, f"Couldn’t

