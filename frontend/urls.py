# frontend/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("quiz/", views.quiz_view, name="quiz"),
    path("quiz/random/", views.random_quiz_view, name="random_quiz"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("register/", views.register_view, name="register"),
    path("login/",    views.login_view,    name="login"),
    path("logout/",   views.logout_view,   name="logout"),
]

