# frontend/urls.py

from django.urls import path
from .views import (
    login_view,
    logout_view,
    register_view,      # ← import this
    quiz_view,
    leaderboard_view,
)

urlpatterns = [
    path("register/",    register_view,     name="register"),   # ← add this
    path("login/",       login_view,        name="login"),
    path("logout/",      logout_view,       name="logout"),
    path("quiz/",        quiz_view,         name="quiz"),
    path("leaderboard/", leaderboard_view,  name="leaderboard"),
]

