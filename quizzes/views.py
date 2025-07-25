# quizzes/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from quiz_logic import generate_quiz as logic_generate_quiz

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

