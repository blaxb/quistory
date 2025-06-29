# quizzes/views.py

from django.db.models import Count, Avg, Max, OuterRef, Subquery, Q
from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

from .models import QuizAttempt
from .serializers import QuizAttemptSerializer, UserLeaderboardSerializer

User = get_user_model()


class QuizAttemptCreateView(generics.CreateAPIView):
    """
    POST here to record a completed quiz attempt.
    """
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes     = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # automatically set request.user as the user field
        serializer.save(user=self.request.user)


class LeaderboardView(generics.ListAPIView):
    """
    Returns users ordered by average percent_correct across unique quizzes,
    only including users with at least 50 total attempts.
    """
    serializer_class   = UserLeaderboardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # 1) Subquery to get best percent_correct per quiz_hash for each user
        best_per_quiz = (
            QuizAttempt.objects
                .filter(user_id=OuterRef("pk"))
                .values("quiz_hash")
                .annotate(best_pct=Max("percent_correct"))
                .values("best_pct")  # Subquery returns best_pct for each hash
        )

        # 2) Annotate each user with:
        #    - total_attempts: raw count of all QuizAttempt
        #    - quizzes_counted: count of distinct quiz_hash where best_pct exists
        #    - avg_percent: average of those best_pct values
        qs = (
            User.objects
                .annotate(
                    total_attempts=Count("quizattempt"),
                )
                .filter(total_attempts__gte=50)  # require ≥50 raw attempts
                .annotate(
                    quizzes_counted=Count(
                        "quizattempt__quiz_hash",
                        distinct=True
                    ),
                    avg_percent=Avg(
                        Subquery(best_per_quiz),
                        output_field=None
                    )
                )
                .order_by("-avg_percent", "-quizzes_counted")
        )
        return qs

