# Generated by Django 5.2.3 on 2025-07-02 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0002_quizattempt_percent_correct_quizattempt_quiz_hash'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quizattempt',
            name='percent_correct',
        ),
        migrations.RemoveField(
            model_name='quizattempt',
            name='quiz_hash',
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='points',
            field=models.IntegerField(default=0),
        ),
    ]
