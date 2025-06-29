from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class QuizAttempt(models.Model):
    user            = models.ForeignKey(User, on_delete=models.CASCADE)
    topic           = models.CharField(max_length=255)
    correct_count   = models.IntegerField()
    total_count     = models.IntegerField()

    # new fields for percent and deduplication
    percent_correct = models.FloatField(null=True, blank=True)
    quiz_hash       = models.CharField(max_length=64, null=True, blank=True)

    timestamp       = models.DateTimeField(auto_now_add=True)

    @property
    def points(self):
        # simple 1 point per correct answer
        return self.correct_count

    class Meta:
        ordering = ['-timestamp']

