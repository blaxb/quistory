from django.urls import path
from .views import (
    generate_quiz,
    QuizAttemptCreateView,
    LeaderboardView,
)

app_name = 'quizzes'

urlpatterns = [
    path("generate-quiz/",    generate_quiz,                  name="generate_quiz"),
    path("attempts/",         QuizAttemptCreateView.as_view(), name="quiz_attempt_create"),
    path("leaderboard/",      LeaderboardView.as_view(),      name="leaderboard"),
]

