import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, TopicForm, RegisterForm

# Base URLs for your two backends
DJANGO_API_BASE = "http://127.0.0.1:8000"  # Django (auth & leaderboard)
QUIZ_API_BASE   = "http://127.0.0.1:8001"  # FastAPI (quiz generation)


def home(request):
    return redirect("quiz")


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        resp = requests.post(
            f"{DJANGO_API_BASE}/api/auth/register/",
            json={
                "username":  form.cleaned_data["username"],
                "email":     form.cleaned_data["email"],
                "password":  form.cleaned_data["password"],
                "password2": form.cleaned_data["password2"],
            }
        )
        if resp.status_code == 201:
            messages.success(request, "Account created! Please log in.")
            return redirect("login")
        else:
            errors = resp.json()
            for field, errs in errors.items():
                form.add_error(field, errs)
    return render(request, "frontend/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        resp = requests.post(
            f"{DJANGO_API_BASE}/api/auth/login/",
            json=form.cleaned_data
        )
        if resp.status_code == 200:
            token = resp.json().get("access")
            request.session["token"] = token
            return redirect("quiz")
        messages.error(request, "Invalid credentials")
    return render(request, "frontend/login.html", {"form": form})


def logout_view(request):
    request.session.pop("token", None)
    return redirect("quiz")


def quiz_view(request):
    form = TopicForm(request.POST or None)
    quiz = None

    if form.is_valid():
        gen = requests.post(
            f"{QUIZ_API_BASE}/generate-quiz",
            json={"topic": form.cleaned_data["topic"]}
        )
        try:
            gen.raise_for_status()
            quiz = gen.json()
        except requests.HTTPError:
            messages.error(request, f"Error generating quiz: {gen.status_code}")

    return render(request, "frontend/quiz.html", {
        "form": form,
        "quiz": quiz,
    })


def leaderboard_view(request):
    resp = requests.get(f"{DJANGO_API_BASE}/api/quiz/leaderboard/")
    resp.raise_for_status()
    leaders = resp.json()
    return render(request, "frontend/leaderboard.html", {
        "leaders": leaders,
    })

