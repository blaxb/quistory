# quizzes/views.py
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import QuizAttempt
from .serializers import QuizAttemptSerializer, UserLeaderboardSerializer

# import your quiz‐generation logic function
# (adjust the path/name if yours is different)
from quiz_logic import generate_quiz as logic_generate_quiz


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_quiz(request):
    """
    POST JSON { "topic": "<some topic>" } 
    → returns a generated quiz dict/JSON.
    """
    topic = request.data.get("topic")
    if not topic:
        return Response(
            {"detail": "Topic field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        quiz = logic_generate_quiz(topic)
    except Exception as e:
        return Response(
            {"detail": f"Error generating quiz: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(quiz, status=status.HTTP_200_OK)


class QuizAttemptCreateView(generics.CreateAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    # put your auth classes here, e.g. IsAuthenticated


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
                    quizzes_played = Count("quizattempt"),
                    total_points   = Coalesce(Sum("quizattempt__points"), Value(0)),
                )
                .filter(quizzes_played__gt=0)
                .order_by("-total_points", "-quizzes_played")[:100]
        )

