import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as dj_login, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import LoginForm, RegisterForm, TopicForm
from quiz_logic import generate_quiz as logic_generate_quiz
from django.db.models import Count, Sum
from django.contrib.auth.models import User


def home(request):
    return redirect("quiz")


def register_view(request):
    """
    Create a Django user directly (no HTTP call to our own API).
    """
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        UserModel = get_user_model()
        username = form.cleaned_data["username"]
        email    = form.cleaned_data.get("email") or ""
        password = form.cleaned_data["password"]

        if UserModel.objects.filter(username=username).exists():
            form.add_error("username", "That username is taken.")
        else:
            try:
                UserModel.objects.create_user(
                    username=username, email=email, password=password
                )
            except Exception as e:
                messages.error(request, f"Couldn’t create account: {e}")
            else:
                messages.success(request, "Account created! Please log in.")
                return redirect("login")
    return render(request, "frontend/register.html", {"form": form})


def login_view(request):
    """
    Authenticate locally and mint JWTs (no HTTP self-call).
    """
    form = LoginForm(request.POST or None)
    if form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if not user:
            messages.error(request, "Invalid username or password.")
        else:
            # Log into Django session (for template conditionals, etc.)
            dj_login(request, user)

            # Mint SimpleJWT tokens and store in session so quiz.js can use them
            refresh = RefreshToken.for_user(user)
            request.session["token"] = str(refresh.access_token)
            request.session["refresh_token"] = str(refresh)

            return redirect("quiz")

    return render(request, "frontend/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    return redirect("quiz")


def quiz_view(request):
    """
    Generate the quiz in-process (no HTTP call).
    """
    form = TopicForm(request.POST or None)
    quiz = None

    if form.is_valid():
        topic = form.cleaned_data["topic"]
        try:
            # logic_generate_quiz returns {"topic": ..., "items": [...]}
            quiz = logic_generate_quiz(topic)
        except Exception as e:
            messages.error(request, f"Couldn’t generate quiz: {e}")

    return render(request, "frontend/quiz.html", {"form": form, "quiz": quiz})


def leaderboard_view(request):
    """
    Build leaderboard via ORM directly (no HTTP).
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
    form  = TopicForm()
    topic = "Pick a random quiz topic and list its items"
    quiz  = None
    try:
        quiz = logic_generate_quiz(topic)
    except Exception as e:
        messages.error(request, f"Couldn’t load random quiz: {e}")

    return render(request, "frontend/quiz.html", {"form": form, "quiz": quiz})

