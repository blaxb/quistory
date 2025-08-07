from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Count, Sum
from django.contrib.auth.models import User

from quiz_logic import generate_quiz as logic_generate_quiz
from .models import QuizAttempt
from .serializers import QuizAttemptSerializer, UserLeaderboardSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_quiz(request):
    topic = request.data.get('topic')
    if not topic:
        return Response({'detail': 'Missing "topic" field.'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        items = logic_generate_quiz(topic)
    except Exception as e:
        return Response({'detail': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(items, status=status.HTTP_200_OK)


class QuizAttemptCreateView(generics.CreateAPIView):
    """
    POST /api/quiz/attempts/ → create a new QuizAttempt
    """
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer


class LeaderboardView(generics.ListAPIView):
    """
    GET /api/quiz/leaderboard/ → top users by total_points
    """
    queryset = (
        User.objects
        .annotate(
            quizzes_played=Count('quizattempt'),
            total_points=Sum('quizattempt__points'),
        )
        .order_by('-total_points')
    )
    serializer_class = UserLeaderboardSerializer

