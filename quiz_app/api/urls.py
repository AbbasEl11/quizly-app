from django.urls import path
from quiz_app.api.views import CreateQuizView

urlpatterns = [
   path('createQuiz/', CreateQuizView.as_view(), name='CreateQuizView'),
]