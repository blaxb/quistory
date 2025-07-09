from django.contrib.auth.models import User
from rest_framework import serializers
from .models import QuizAttempt

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model  = QuizAttempt
        fields = [
            'id',
            'topic',
            'correct_count',
            'total_count',
            'points',
            'quiz_hash',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Automatically associate the currently-logged-in user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserLeaderboardSerializer(serializers.ModelSerializer):
    quizzes_played = serializers.IntegerField()
    total_points   = serializers.IntegerField()

    class Meta:
        model  = User
        fields = ['username', 'quizzes_played', 'total_points']

