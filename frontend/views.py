# frontend/views.py

import os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from requests.exceptions import RequestException

from .forms import LoginForm, RegisterForm, TopicForm

# For auth endpoints only (can still use your API if you want)
DJANGO_API_BASE = os.environ.get("DJANGO_API_BASE", "http://127.0.0.1:8000")

# --- NEW: use the quiz logic directly (no HTTP call to ourselves) ---
from quiz_logic import generate_quiz as logic_generate_quiz
from django.db.models import Count, Sum
from django.contrib.auth.models import User


def home(request):
    return redirect("quiz")


def register_view(request):
    """
    Keeps using your REST auth endpoint.
    If you see timeouts here too, set WEB_CONCURRENCY=2 on Render.
    """
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
                timeout=15,
            )
            resp.raise_for_status()
        except RequestException as e:
            messages.error(request, f"Registration service error: {e}")
        else:
            if resp.status_code == 201:
                messages.success(request, "Account created! Please log in.")
                return redirect("login")
            for field, errs in resp.json().items():
                form.add_error(field, errs)
    return render(request, "frontend/register.html", {"form": form})


def login_view(request):
    """
    Keeps using your REST auth endpoint.
    If you see timeouts here too, set WEB_CONCURRENCY=2 on Render.
    """
    form = LoginForm(request.POST or None)
    if form.is_valid():
        try:
            resp = requests.post(
                f"{DJANGO_API_BASE}/api/auth/login/",
                json=form.cleaned_data,
                timeout=15,
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
    NO HTTP round-trip. Generate using local Python, then render the page.
    """
    form = TopicForm(request.POST or None)
    quiz = None

    if form.is_valid():
        topic = form.cleaned_data["topic"]
        try:
            quiz = logic_generate_quiz(topic)  # returns {"topic": ..., "items": [...]}
        except Exception as e:
            messages.error(request, f"Couldn’t generate quiz: {e}")
            quiz = None

    return render(request, "frontend/quiz.html", {
        "form": form,
        "quiz": quiz,
    })


def leaderboard_view(request):
    """
    NO HTTP round-trip. Query directly via ORM and pass a simple list of dicts.
    """
    leaders_qs = (
        User.objects
        .annotate(
            quizzes_played=Count('quizattempt'),
            total_points=Sum('quizattempt__points'),
        )
        .order_by('-total_points')
    )
    leaders = [
        {
            "username": u.username,
            "quizzes_played": u.quizzes_played or 0,
            "total_points": u.total_points or 0,
        }
        for u in leaders_qs
    ]
    return render(request, "frontend/leaderboard.html", {"leaders": leaders})


def random_quiz_view(request):
    """
    NO HTTP round-trip. Generate locally with a canned prompt.
    """
    form  = TopicForm()
    topic = "Pick a random quiz topic and list its items"
    quiz  = None
    try:
        quiz = logic_generate_quiz(topic)
    except Exception as e:
        messages.error(request, f"Couldn’t load random quiz: {e}")

    return render(request, "frontend/quiz.html", {
        "form":  form,
        "quiz":  quiz,
    })

