import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, RegisterForm, TopicForm

# your two backends
DJANGO_API_BASE = "http://127.0.0.1:8000"
QUIZ_API_BASE   = "http://127.0.0.1:8001"


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
            for field, errs in resp.json().items():
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
            data = resp.json()
            # store both tokens
            request.session["token"]         = data.get("access")
            request.session["refresh_token"] = data.get("refresh")
            return redirect("quiz")
        messages.error(request, "Invalid credentials")
    return render(request, "frontend/login.html", {"form": form})


def logout_view(request):
    # clear everything
    request.session.flush()
    return redirect("quiz")


def quiz_view(request):
    form = TopicForm(request.POST or None)
    quiz = None
    if form.is_valid():
        gen = requests.post(
            f"{QUIZ_API_BASE}/generate-quiz",
            json={"topic": form.cleaned_data["topic"]}
        )
        if gen.status_code == 200:
            quiz = gen.json()
        else:
            messages.error(request, f"Error generating quiz: {gen.status_code}")
    return render(request, "frontend/quiz.html", {
        "form": form,
        "quiz": quiz,
    })


def leaderboard_view(request):
    resp = requests.get(f"{DJANGO_API_BASE}/api/quiz/leaderboard/")
    resp.raise_for_status()
    return render(request, "frontend/leaderboard.html", {
        "leaders": resp.json(),
    })


def random_quiz_view(request):
    form  = TopicForm()
    topic = "Pick a random quiz topic and list its items"
    try:
        resp = requests.post(
            f"{QUIZ_API_BASE}/generate-quiz",
            json={"topic": topic}
        )
        resp.raise_for_status()
        quiz = resp.json()
    except requests.HTTPError as e:
        messages.error(request, f"Couldn’t load random quiz ({e.response.status_code})")
        return redirect("quiz")
    return render(request, "frontend/quiz.html", {
        "form":  form,
        "quiz":  quiz,
        "topic": topic,
    })

