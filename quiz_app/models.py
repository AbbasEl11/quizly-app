from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    """
    Quiz model representing a quiz generated from a YouTube video.
    
    Attributes:
        user: ForeignKey to User who created the quiz
        title: Title of the quiz (max 255 chars)
        description: Detailed description of the quiz
        created_at: Auto-generated timestamp when quiz was created
        updated_at: Auto-updated timestamp when quiz was last modified
        video_url: URL of the YouTube video used to generate the quiz
    """
    user = models.ForeignKey(User, related_name='quizzes', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Question model representing a single quiz question with multiple choice options.
    
    Attributes:
        quiz: ForeignKey to the Quiz this question belongs to
        question_title: The question text (max 255 chars)
        question_options: JSON array of 4 answer options
        answer: The correct answer (must be one of the options)
        created_at: Auto-generated timestamp when question was created
        updated_at: Auto-updated timestamp when question was last modified
    """
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_title = models.CharField(max_length=255)
    question_options = models.JSONField(default=list)
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question_title} (Quiz: {self.quiz.title})"