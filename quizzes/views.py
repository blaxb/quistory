# quizzes/views.py

import asyncio

from django.contrib.auth.models import User
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import QuizAttempt
from .serializers import QuizAttemptSerializer, UserLeaderboardSerializer

from fallback_gpt import generate_quiz_with_gpt


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


@api_view(['POST'])
def generate_quiz(request):
    """
    POST {"topic": "..."} → 200 {"topic": "...", "items": [ ... ] }
    """
    topic = request.data.get('topic')
    if not topic:
        return Response(
            {'detail': 'Missing "topic" in request body'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # run the async generator and get a List[str]
        items = asyncio.run(generate_quiz_with_gpt(topic))
    except Exception as exc:
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({'topic': topic, 'items': items})

