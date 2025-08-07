# frontend/views.py
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, RegisterForm, TopicForm


def _api_base(request):
    # e.g. "https://quistory.onrender.com"
    return request.build_absolute_uri("/").rstrip("/")


def home(request):
    return redirect("quiz")


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        url = f"{_api_base(request)}/api/auth/register/"
        try:
            resp = requests.post(
                url,
                json={
                    "username":  form.cleaned_data["username"],
                    "email":     form.cleaned_data["email"],
                    "password":  form.cleaned_data["password"],
                    "password2": form.cleaned_data["password2"],
                },
                timeout=5,
            )
            resp.raise_for_status()
        except Exception as e:
            messages.error(request, f"Registration error: {e}")
        else:
            if resp.status_code == 201:
                messages.success(request, "Account created! Please log in.")
                return redirect("login")
            for field, errs in resp.json().items():
                form.add_error(field, errs)
    return render(request, "frontend/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        url = f"{_api_base(request)}/api/auth/login/"
        try:
            resp = requests.post(url, json=form.cleaned_data, timeout=5)
            resp.raise_for_status()
        except Exception as e:
            messages.error(request, f"Login error: {e}")
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

    if request.method == "POST" and form.is_valid():
        url = f"{_api_base(request)}/api/quiz/generate-quiz/"
        try:
            resp = requests.post(
                url,
                json={"topic": form.cleaned_data["topic"]},
                timeout=10,
            )
            resp.raise_for_status()
            quiz = resp.json()
        except Exception as e:
            messages.error(request, f"Couldn’t generate quiz: {e}")

    return render(request, "frontend/quiz.html", {
        "form": form,
        "quiz": quiz,
    })


def leaderboard_view(request):
    url = f"{_api_base(request)}/api/quiz/leaderboard/"
    leaders = []
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        leaders = resp.json()
    except Exception as e:
        messages.error(request, f"Couldn’t load leaderboard: {e}")

    return render(request, "frontend/leaderboard.html", {
        "leaders": leaders,
    })


def random_quiz_view(request):
    form  = TopicForm()
    topic = "Pick a random quiz topic and list its items"
    quiz  = None

    url = f"{_api_base(request)}/api/quiz/generate-quiz/"
    try:
        resp = requests.post(
            url,
            json={"topic": topic},
            timeout=10,
        )
        resp.raise_for_status()
        quiz = resp.json()
    except Exception as e:
        messages.error(request, f"Couldn’t load random quiz: {e}")

    return render(request, "frontend/quiz.html", {
        "form":  form,
        "quiz":  quiz,
        "topic": topic,
    })

