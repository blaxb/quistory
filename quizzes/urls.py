# quizzes/urls.py
from django.urls import path
from .views import QuizAttemptCreateView, LeaderboardView

urlpatterns = [
    # POST   /api/quiz/attempts/    → QuizAttemptCreateView
    path("attempts/",   QuizAttemptCreateView.as_view(), name="attempt-create"),
    # GET    /api/quiz/leaderboard/ → LeaderboardView
    path("leaderboard/", LeaderboardView.as_view(),   name="leaderboard"),
]

