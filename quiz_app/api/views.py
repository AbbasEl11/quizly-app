from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied

from quiz_app.models import Quiz
from quiz_app.api.serializers import QuizSerializer, CreateQuestionSerializer
from quiz_app.api.services import QuizService


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
        
        try:
            quiz = QuizService.create_quiz_from_youtube(
                user=request.user,
                video_url=video_url
            )
            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        Retrieve all quizzes for the authenticated user.
        
        Returns:
            Response: List of quizzes owned by the user (200)
        """
        quizzes = QuizService.get_user_quizzes(request.user)
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
            quiz = QuizService.get_quiz_by_id(pk)

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
            quiz = QuizService.get_quiz_by_id(pk)

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
            quiz = QuizService.get_quiz_by_id(pk)

            if request.user != quiz.user:
                raise PermissionDenied("You do not have permission to delete this quiz.")
             
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": "You have not Permission to delete this Quiz"}, status=status.HTTP_403_FORBIDDEN)

        QuizService.delete_quiz(quiz)
        return Response(status=status.HTTP_204_NO_CONTENT)