from rest_framework import serializers
from quiz_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Question model.
    
    Serializes question data including title, options, correct answer, and timestamps.
    Used for read operations in quiz retrieval.
    """
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for Quiz model with nested questions.
    
    Includes all quiz fields and nested QuestionSerializer for related questions.
    Used for full quiz data representation in API responses.
    """
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at', 'updated_at', 'questions']


class CreateQuestionSerializer(serializers.Serializer):
    """
    Serializer for quiz creation from YouTube URL.
    
    Validates YouTube URL input for quiz generation endpoint.
    """
    url = serializers.URLField()


class UpdateQuizSerializer(serializers.ModelSerializer):
    """
    Serializer for partial quiz updates (PATCH operations).
    
    Allows updating only title and description fields.
    All fields are optional to support partial updates.
    """
    class Meta:
        model = Quiz
        fields = ['title', 'description']
        extra_kwargs = {
            'title': {'required': False, "allow_blank": False},
            'description': {'required': False, "allow_blank": True},
        }