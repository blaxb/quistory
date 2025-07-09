# quizzes/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    correct_count = models.IntegerField()
    total_count   = models.IntegerField()

    # Now with defaults to avoid migration prompts:
    percent_correct = models.IntegerField(default=0)
    quiz_hash       = models.CharField(max_length=64, default="")

    # Persisted points from client-side calculation
    points = models.IntegerField(default=0)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

