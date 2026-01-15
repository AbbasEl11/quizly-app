import tempfile
from django.db import transaction
from quiz_app.models import Quiz, Question
from quiz_app.api.utils import (
    extract_video_id,
    download_audio,
    transcribe_audio,
    generate_quiz_with_gemini,
    validate_quiz_json
)


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


class QuizService:
    """
    Service layer for quiz-related business logic.
    Handles quiz creation from YouTube videos including audio processing,
    transcription, and AI-generated question generation.
    """

    @staticmethod
    def create_quiz_from_youtube(user, video_url):
        """
        Create a complete quiz from a YouTube video URL.
        
        This method orchestrates the entire quiz creation process:
        1. Extract and validate YouTube video ID
        2. Download audio from video
        3. Transcribe audio to text
        4. Generate quiz questions using AI
        5. Validate generated quiz structure
        6. Save quiz and questions to database
        
        Args:
            user: The User instance who owns the quiz
            video_url: YouTube video URL string
            
        Returns:
            Quiz: The created Quiz instance with all questions
            
        Raises:
            ValueError: If YouTube URL is invalid or quiz validation fails
            RuntimeError: If transcription fails
            Exception: For any other processing errors
        """
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL.")
        
        # Process audio and generate transcript
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = download_audio(video_url, tmp_dir)
            transcript = transcribe_audio(audio_path)
        
        if not transcript:
            raise RuntimeError("Transcription failed.")
        
        # Generate quiz using AI
        prompt = PROMPT_TEMPLATE.format(transcript=transcript)
        quiz_json = generate_quiz_with_gemini(prompt)

        # Validate quiz structure
        ok, err = validate_quiz_json(quiz_json)
        if not ok:
            raise ValueError(f"Generated quiz is invalid: {err}")
        
        # Save to database
        return QuizService._save_quiz_to_database(user, video_url, quiz_json)
    
    @staticmethod
    def _save_quiz_to_database(user, video_url, quiz_json):
        """
        Save quiz and associated questions to database in a transaction.
        
        Args:
            user: User instance who owns the quiz
            video_url: YouTube video URL
            quiz_json: Validated quiz data dictionary
            
        Returns:
            Quiz: Created Quiz instance with all questions
        """
        with transaction.atomic():
            quiz = Quiz.objects.create(
                user=user,
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

        return quiz
    
    @staticmethod
    def get_user_quizzes(user):
        """
        Retrieve all quizzes for a specific user.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet: All Quiz instances owned by the user
        """
        return Quiz.objects.filter(user=user)
    
    @staticmethod
    def get_quiz_by_id(quiz_id):
        """
        Retrieve a quiz by its ID.
        
        Args:
            quiz_id: Primary key of the quiz
            
        Returns:
            Quiz: Quiz instance
            
        Raises:
            Quiz.DoesNotExist: If quiz not found
        """
        return Quiz.objects.get(pk=quiz_id)
    
    @staticmethod
    def update_quiz(quiz, data):
        """
        Update quiz fields with provided data.
        
        Args:
            quiz: Quiz instance to update
            data: Dictionary with fields to update
            
        Returns:
            Quiz: Updated quiz instance
        """
        for field, value in data.items():
            if hasattr(quiz, field):
                setattr(quiz, field, value)
        quiz.save()
        return quiz
    
    @staticmethod
    def delete_quiz(quiz):
        """
        Delete a quiz and all associated questions.
        
        Args:
            quiz: Quiz instance to delete
        """
        quiz.delete()
