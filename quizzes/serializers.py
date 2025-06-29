from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import QuizAttempt

User = get_user_model()

class QuizAttemptSerializer(serializers.ModelSerializer):
    # Expose the model’s points property
    points = serializers.IntegerField(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "topic",
            "correct_count",
            "total_count",
            "percent_correct",
            "quiz_hash",
            "timestamp",
            "points",
        )
        read_only_fields = (
            "id",
            "user",
            "timestamp",
            "points",
        )


class UserLeaderboardSerializer(serializers.ModelSerializer):
    # Number of unique quizzes (by quiz_hash) counted
    quizzes_counted = serializers.IntegerField(read_only=True)
    # Total raw attempts
    total_attempts = serializers.IntegerField(read_only=True)
    # Average percent_correct across unique quizzes
    avg_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "quizzes_counted",
            "total_attempts",
            "avg_percent",
        )

