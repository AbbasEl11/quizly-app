import tempfile

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from quiz_app.api.utils import extract_video_id, download_audio,transcribe_audio, generate_quiz_with_gemini, validate_quiz_json

from quiz_app.models import Quiz, Question
from quiz_app.api.serializers import QuizSerializer, QuestionSerializer, CreateQuestionSerializer

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_url = serializer.validated_data['url']
        video_id = extract_video_id(video_url)

        if not extract_video_id(video_url):
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
                    user = request.user,
                    title = str(quiz_json.get("title", "")).strip(),
                    description = str(quiz_json.get("description", "")).strip(),
                    video_url = video_url,
                )

                for q in quiz_json.get("questions", []):
                    Question.objects.create(
                        quiz = quiz,
                        question_title = str(q.get("question_title", "")).strip(),
                        question_options = q.get("question_options", []),
                        answer = str(q.get("answer", "")).strip(),
                    )

            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
