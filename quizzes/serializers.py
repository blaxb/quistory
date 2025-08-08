from rest_framework import serializers
from django.contrib.auth.models import User
from .models import QuizAttempt


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = [
            "id", "user", "topic",
            "correct_count", "total_count",
            "quiz_hash", "points", "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class UserLeaderboardSerializer(serializers.ModelSerializer):
    quizzes_played = serializers.IntegerField()
    total_points = serializers.IntegerField()

    class Meta:
        model = User
        fields = ["username", "quizzes_played", "total_points"]

