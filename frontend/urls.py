from django.urls import path
from .views import home, login_view, logout_view, register_view, quiz_view, leaderboard_view

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("quiz/",  quiz_view, name="quiz"),
    path("leaderboard/", leaderboard_view, name="leaderboard"),
]

