kimport os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from requests.exceptions import RequestException
from .forms import LoginForm, RegisterForm, TopicForm

# Backends (override via env vars in production)
DJANGO_API_BASE = os.environ.get("DJANGO_API_BASE", "http://127.0.0.1:8000")
QUIZ_API_BASE   = os.environ.get("QUIZ_API_BASE", "http://127.0.0.1:8001")


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
                timeout=5,
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
    form = LoginForm(request.POST or None)
    if form.is_valid():
        try:
            resp = requests.post(
                f"{DJANGO_API_BASE}/api/auth/login/",
                json=form.cleaned_data,
                timeout=5,
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
    form = TopicForm(request.POST or None)
    quiz = None

    if form.is_valid():
        try:
            gen = requests.post(
                f"{QUIZ_API_BASE}/generate-quiz",
                json={"topic": form.cleaned_data["topic"]},
                timeout=5,
            )
            gen.raise_for_status()
        except RequestException as e:
            messages.error(request, f"Couldn’t generate quiz: {e}")
        else:
            quiz = gen.json()

    return render(request, "frontend/quiz.html", {
        "form": form,
        "quiz": quiz,
    })


def leaderboard_view(request):
    try:
        resp = requests.get(
            f"{DJANGO_API_BASE}/api/quiz/leaderboard/",
            timeout=5,
        )
        resp.raise_for_status()
    except RequestException as e:
        messages.error(request, f"Couldn’t load leaderboard: {e}")
        leaders = []
    else:
        leaders = resp.json()

    return render(request, "frontend/leaderboard.html", {
        "leaders": leaders,
    })


def random_quiz_view(request):
    form  = TopicForm()
    topic = "Pick a random quiz topic and list its items"
    quiz  = None

    try:
        resp = requests.post(
            f"{QUIZ_API_BASE}/generate-quiz",
            json={"topic": topic},
            timeout=5,
        )
        resp.raise_for_status()
    except RequestException as e:
        messages.error(request, f"Couldn’t load random quiz: {e}")
    else:
        quiz = resp.json()

    return render(request, "frontend/quiz.html", {
        "form":  form,
        "quiz":  quiz,
        "topic": topic,
    })

