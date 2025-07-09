from django.contrib.auth.models import User
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import QuizAttempt
from .serializers import QuizAttemptSerializer, UserLeaderboardSerializer

class QuizAttemptCreateView(generics.CreateAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    # keep whatever auth you had here (e.g. IsAuthenticated)

class LeaderboardView(generics.ListAPIView):
    """
    Returns up to the top-100 users ordered by total points,
    annotated with quizzes_played and total_points.
    """
    serializer_class   = UserLeaderboardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            User.objects
                .annotate(
                    quizzes_played = Count('quizattempt'),
                    total_points   = Coalesce(Sum('quizattempt__points'), Value(0)),
                )
                .filter(quizzes_played__gt=0)
                .order_by('-total_points', '-quizzes_played')[:100]
        )

