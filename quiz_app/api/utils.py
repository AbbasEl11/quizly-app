import re
import json
import os
from urllib.parse import urlparse, parse_qs
from yt_dlp.utils import DownloadError
from google import genai

from yt_dlp import YoutubeDL
from django.conf import settings


YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be"}


def extract_video_id(url: str) -> str | None:
    """
    Extract YouTube video ID from various YouTube URL formats.
    
    Supports:
    - youtube.com/watch?v=VIDEO_ID
    - youtu.be/VIDEO_ID
    - youtube.com/shorts/VIDEO_ID
    - youtube.com/embed/VIDEO_ID
    
    Args:
        url: YouTube video URL
        
    Returns:
        str | None: Video ID if valid YouTube URL, None otherwise
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    
    host = (parsed.netloc or "").lower()
    if host not in YOUTUBE_DOMAINS:
        return None
    
    if host == "youtu.be":
        vid = parsed.path.strip("/").split("/")[0]
        return vid or None
    
    if parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]
    
    m = re.match(r"^/shorts/([^/]+)", parsed.path)
    if m: 
        return m.group(1)

    m = re.match(r"^/embed/([^/]+)", parsed.path)
    if m:
        return m.group(1)
    return None


def download_audio(video_url: str, tmp_dir: str) -> str:
    """
    Download audio from YouTube video and convert to MP3.
    
    Uses yt-dlp to download best audio quality and FFmpeg to convert to MP3.
    
    Args:
        video_url: YouTube video URL
        tmp_dir: Temporary directory path for saving audio file
        
    Returns:
        str: Path to downloaded MP3 file
        
    Raises:
        Exception: If download or audio extraction fails
    """
    outtmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        "noplayslist": True,
        "quiet": True,
        "no_warnings": True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try: 
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except DownloadError as e:
        raise Exception("Failed to download audio.") from e
    
    audio_path = os.path.join(tmp_dir, "audio.mp3")
    if not os.path.exists(audio_path):
        raise Exception("Audio extraction failed.")
    return audio_path

_WHISPER_MODEL = None


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using OpenAI Whisper.
    
    Lazy-loads Whisper model on first use and caches it for subsequent calls.
    Model type can be configured via settings.WHISPER_MODEL (default: "base").
    
    Args:
        audio_path: Path to audio file (MP3, WAV, etc.)
        
    Returns:
        str: Transcribed text from audio
    """
    global _WHISPER_MODEL
    import whisper

    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = whisper.load_model(getattr(settings, "WHISPER_MODEL", "base"))

    result = _WHISPER_MODEL.transcribe(audio_path)
    return (result or {}).get("text", "").strip()


def generate_quiz_with_gemini(prompt: str) -> dict:
    """
    Generate quiz questions using Google Gemini AI.
    
    Sends prompt to Gemini API and parses JSON response containing quiz data.
    Handles JSON code blocks (```json) in response.
    
    Args:
        prompt: Formatted prompt with transcript for quiz generation
        
    Returns:
        dict: Parsed JSON containing quiz title, description, and questions
        
    Raises:
        Exception: If GEMINI_API_KEY not set or response is not valid JSON
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set in settings.")
    
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(model=model, contents=prompt)

    text = (response.text or  "").strip()

    if text.startswith("```json"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    
    try:
        return json.loads(text)
    except Exception:
        raise Exception("Generated content is not valid JSON.")


def validate_quiz_json(q: dict) -> tuple[bool, str]:
    """
    Validate quiz JSON structure and content.
    
    Checks for:
    - Required keys (title, description, questions)
    - Description length (max 500 chars)
    - Exactly 10 questions
    - Each question has title, 4 distinct options, and valid answer
    
    Args:
        q: Quiz dictionary to validate
        
    Returns:
        tuple[bool, str]: (True, "") if valid, (False, error_message) otherwise
    """
    if not isinstance(q, dict):
        return False, "Quiz is not a JSON object."

    for key in ("title", "description", "questions"):
        if key not in q:
            return False, f"Missing key: {key}"

    if not isinstance(q["description"], str) or len(q["description"]) > 500:
        return False, "description must be <= 500 characters."

    questions = q["questions"]
    if not isinstance(questions, list) or len(questions) != 10:
        return False, "questions must contain exactly 10 questions."

    for i, item in enumerate(questions, start=1):
        qt = item.get("question_title")
        opts = item.get("question_options")
        ans = item.get("answer")

        if not isinstance(qt, str) or not qt.strip():
            return False, f"Q{i}: question_title missing/invalid."
        if not isinstance(opts, list) or len(opts) != 4:
            return False, f"Q{i}: must have exactly 4 options."
        if len(set(opts)) != 4:
            return False, f"Q{i}: options must be distinct."
        if not isinstance(ans, str) or ans not in opts:
            return False, f"Q{i}: answer must be one of the options."

    return True, ""