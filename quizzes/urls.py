from django.urls import path
from .views import QuizAttemptCreateView, LeaderboardView

urlpatterns = [
    # create a quiz attempt
    path("attempts/",    QuizAttemptCreateView.as_view(), name="quiz-attempts"),

    # list the leaderboard
    path("leaderboard/", LeaderboardView.as_view(),       name="quiz-leaderboard"),
]

