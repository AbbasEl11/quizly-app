from rest_framework import serializers
from quiz_app.models import Quiz, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at', 'updated_at', 'questions']

class CreateQuestionSerializer(serializers.Serializer):
    url = serializers.URLField()

class UpdateQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['title', 'description']
        extra_kwargs = {
            'title': {'required': False, "allow_blank": False},
            'description': {'required': False, "allow_blank": True},
        }