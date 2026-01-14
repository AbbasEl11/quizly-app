import tempfile

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from quiz_app.api.utils import (
    extract_video_id,
    download_audio,
    transcribe_audio,
    generate_quiz_with_gemini,
    validate_quiz_json
)
from django.core.exceptions import PermissionDenied

from quiz_app.models import Quiz, Question
from quiz_app.api.serializers import QuizSerializer, CreateQuestionSerializer

PROMPT_TEMPLATE = """
Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }}
    (exactly 10 questions)
  ]
}}

Requirements:
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question, and it must be present in 'question_options'.
- The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
- Do not include explanations, comments, or any text outside the JSON.

Transcript:
{transcript}
""".strip()


class CreateQuizView(APIView):
    """
    API view for creating new quizzes from YouTube videos and listing user's quizzes.
    
    POST: Creates a quiz by downloading audio from YouTube URL, transcribing it,
          and generating quiz questions using Gemini AI.
    GET: Returns all quizzes belonging to the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new quiz from a YouTube video URL.
        
        Args:
            request: HTTP request containing 'url' field with YouTube video URL
            
        Returns:
            Response: Created quiz with questions (201) or error message (400/500)
        """
        serializer = CreateQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_url = serializer.validated_data['url']
        video_id = extract_video_id(video_url)

        if not video_id:
            return Response({"error": "Invalid YouTube URL."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                audio_path = download_audio(video_url, tmp_dir)
                transcript = transcribe_audio(audio_path)
            
            if not transcript:
                return Response({"error": "Transcription failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            prompt = PROMPT_TEMPLATE.format(transcript=transcript)
            quiz_json = generate_quiz_with_gemini(prompt)

            ok, err = validate_quiz_json(quiz_json)
            if not ok:
                return Response({"error": f"Generated quiz is invalid: {err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    user=request.user,
                    title=str(quiz_json.get("title", "")).strip(),
                    description=str(quiz_json.get("description", "")).strip(),
                    video_url=video_url,
                )

                for q in quiz_json.get("questions", []):
                    Question.objects.create(
                        quiz=quiz,
                        question_title=str(q.get("question_title", "")).strip(),
                        question_options=q.get("question_options", []),
                        answer=str(q.get("answer", "")).strip(),
                    )

            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        Retrieve all quizzes for the authenticated user.
        
        Returns:
            Response: List of quizzes owned by the user (200)
        """
        quizzes = Quiz.objects.filter(user=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetQuizByIdView(APIView):
    """
    API view for retrieving, updating, and deleting individual quizzes.
    
    Only the quiz owner has permission to access, modify, or delete a quiz.
    Returns 404 if quiz doesn't exist, 403 if user doesn't own the quiz.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Retrieve a specific quiz by ID.
        
        Args:
            pk: Primary key of the quiz
            
        Returns:
            Response: Quiz data (200), 404 if not found, 403 if no permission
        """
        try:
            quiz = Quiz.objects.get(pk=pk)

            if request.user != quiz.user:
                raise PermissionDenied("You do not have permission to access this quiz.")
             
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": "You have not Permission to enter this Quiz"}, status=status.HTTP_403_FORBIDDEN)

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Partially update a quiz (title, description, etc.).
        
        Args:
            pk: Primary key of the quiz
            
        Returns:
            Response: Updated quiz data (200), 404 if not found, 403 if no permission
        """
        try:
            quiz = Quiz.objects.get(pk=pk)

            if request.user != quiz.user:
                raise PermissionDenied("You do not have permission to modify this quiz.")
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": "You have not Permission to modify this Quiz"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete a quiz and all its associated questions.
        
        Args:
            pk: Primary key of the quiz
            
        Returns:
            Response: 204 on success, 404 if not found, 403 if no permission
        """
        try:
            quiz = Quiz.objects.get(pk=pk)

            if request.user != quiz.user:
                raise PermissionDenied("You do not have permission to delete this quiz.")
             
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": "You have not Permission to delete this Quiz"}, status=status.HTTP_403_FORBIDDEN)

        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)