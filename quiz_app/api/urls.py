"""
URL configuration for Quiz API endpoints.

Provides routes for:
- Creating quizzes from YouTube videos
- Retrieving all user quizzes
- Getting, updating, and deleting specific quizzes by ID
"""
from django.urls import path
from quiz_app.api.views import CreateQuizView, GetQuizByIdView

urlpatterns = [
   path('createQuiz/', CreateQuizView.as_view(), name='CreateQuizView'),
   path('quizzes/', CreateQuizView.as_view(), name='get_quizzes'),
   path('quizzes/<int:pk>/', GetQuizByIdView.as_view(), name='get_quizzes_by_id'),
]