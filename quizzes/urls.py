# quizzes/urls.py

from django.urls import path
from .views import generate_quiz, QuizAttemptCreateView, LeaderboardView

urlpatterns = [
    path("generate-quiz/", generate_quiz, name="generate_quiz"),
    path("attempts/",      QuizAttemptCreateView.as_view(), name="quizattempt-create"),
    path("leaderboard/",   LeaderboardView.as_view(),       name="leaderboard"),
]

