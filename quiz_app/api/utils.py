import re
import json
import os
import tempfile
import requests
from urllib.parse import urlparse, parse_qs
from yt_dlp.utils import DownloadError
from google import genai

from yt_dlp import YoutubeDL
from django.conf import settings


YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be"
}

def extract_video_id(url: str) -> str | None:
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

def download_audio(video_url: str, tmp_dir:str) -> str:
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
    global _WHISPER_MODEL
    import whisper

    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = whisper.load_model(getattr(settings, "WHISPER_MODEL", "base"))

    result = _WHISPER_MODEL.transcribe(audio_path)
    return (result or {}).get("text", "").strip()

def generate_quiz_with_gemini(prompt: str) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set in settings.")
    
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(model=model, contents = prompt)

    text = (response.text or  "").strip()

    if text.startswith("```json"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    
    try:
        return json.loads(text)
    except Exception:
        raise Exception("Generated content is not valid JSON.")
    
def validate_quiz_json(q: dict) -> tuple[bool, str]:
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