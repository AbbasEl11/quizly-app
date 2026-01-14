# Quizly - AI-Powered Quiz Generator

Quizly is a full-stack application that generates interactive quizzes from YouTube videos using AI. The backend API (this repository) handles video processing, transcription, and quiz generation. It automatically downloads audio, transcribes it using Whisper AI, and generates quiz questions using Google Gemini AI.

## Features

- 🎥 **YouTube Video Processing**: Extract audio from YouTube videos
- 🎤 **Speech-to-Text**: Transcribe audio using OpenAI Whisper
- 🤖 **AI Quiz Generation**: Generate 10-question quizzes using Google Gemini Flash
- 🔐 **JWT Authentication**: Secure authentication with HTTP-only cookies
- 👤 **User Management**: User registration, login, logout, token refresh
- 📝 **Quiz Management**: Create, retrieve, update, and delete quizzes
- 🔒 **Permission Control**: Users can only access their own quizzes
- 🎯 **Admin Panel**: Manage quizzes and questions through Django admin

## Tech Stack

### Backend (This Repository)
- **Framework**: Django 6.x, Django REST Framework
- **Authentication**: Simple JWT with HTTP-only cookies
- **AI/ML**: OpenAI Whisper, Google Gemini AI
- **Media Processing**: yt-dlp, FFmpeg
- **Database**: SQLite (development), PostgreSQL recommended for production
- **CORS**: django-cors-headers for frontend integration

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **FFmpeg** (required for audio processing)
- **pip** (Python package manager)

### Installing FFmpeg

#### Windows
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to system PATH
4. Verify: `ffmpeg -version`

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/AbbasEl11/quizly-app
cd quizly_app
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root (or add to `core/settings.py`):

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp

# Whisper Model (options: tiny, base, small, medium, large)
WHISPER_MODEL=base

# JWT Settings (optional - defaults are fine)
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

**Getting API Keys:**
- **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (for Admin Panel)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Authentication

#### Register User
```http
POST /api/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123"
}
```

#### Login
```http
POST /api/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123"
}
```
**Response**: Sets HTTP-only cookies (`access_token`, `refresh_token`)

#### Logout
```http
POST /api/logout/
Authorization: Bearer <access_token>
```
**Response**: Deletes cookies and blacklists refresh token

#### Refresh Token
```http
POST /api/token/refresh/
```
**Note**: Uses `refresh_token` from cookies

### Quiz Management

#### Create Quiz from YouTube Video
```http
POST /api/createQuiz/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```
**Response**: Quiz with 10 auto-generated questions

#### Get All User Quizzes
```http
GET /api/quizzes/
Authorization: Bearer <access_token>
```

#### Get Specific Quiz
```http
GET /api/quizzes/{id}/
Authorization: Bearer <access_token>
```

#### Update Quiz
```http
PATCH /api/quizzes/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Quiz
```http
DELETE /api/quizzes/{id}/
Authorization: Bearer <access_token>
```

## Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 204  | No Content (Delete success) |
| 400  | Bad Request (Invalid data) |
| 401  | Unauthorized (Invalid/missing token) |
| 403  | Forbidden (No permission) |
| 404  | Not Found |
| 500  | Internal Server Error |

## Project Structure

```
quizly_app/
├── auth_app/              # Authentication app
│   ├── api/
│   │   ├── views.py       # Login, Register, Logout, Refresh
│   │   ├── serializers.py
│   │   └── urls.py
│   └── authentication.py  # Custom JWT authentication
├── quiz_app/              # Quiz management app
│   ├── api/
│   │   ├── views.py       # Quiz CRUD operations
│   │   ├── serializers.py
│   │   ├── utils.py       # YouTube, Whisper, Gemini utilities
│   │   └── urls.py
│   ├── models.py          # Quiz and Question models
│   └── admin.py           # Admin configuration
├── core/                  # Django project settings
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── db.sqlite3
```

## Models

### Quiz
```python
{
  "id": 1,
  "user": 1,
  "title": "Python Basics Quiz",
  "description": "A quiz about Python fundamentals",
  "video_url": "https://youtube.com/watch?v=...",
  "created_at": "2026-01-14T10:00:00Z",
  "updated_at": "2026-01-14T10:00:00Z",
  "questions": [...]
}
```

### Question
```python
{
  "id": 1,
  "quiz": 1,
  "question_title": "What is Python?",
  "question_options": [
    "A programming language",
    "A snake",
    "A framework",
    "A database"
  ],
  "answer": "A programming language",
  "created_at": "2026-01-14T10:00:00Z",
  "updated_at": "2026-01-14T10:00:00Z"
}
```

## Admin Panel

Access the admin panel at: `http://localhost:8000/admin`

**Features:**
- View and manage all quizzes
- Edit quiz details and questions inline
- Filter by user, creation date
- Search by title, description, username

## Security Features

- ✅ JWT tokens stored in HTTP-only cookies (XSS protection)
- ✅ CSRF protection enabled
- ✅ Refresh token blacklisting on logout
- ✅ Permission-based access control (users can only access own quizzes)
- ✅ Validation for all user inputs
- ✅ Secure cookie flags (httponly, secure, samesite)

## Troubleshooting

### FFmpeg Not Found
**Error**: `ffmpeg not found`
**Solution**: Install FFmpeg and add to system PATH (see Prerequisites)

### Gemini API Error
**Error**: `GEMINI_API_KEY is not set`
**Solution**: Add `GEMINI_API_KEY` to settings or `.env` file

### Whisper Model Loading Slow
**Solution**: First-time download of Whisper model can be slow. Use `WHISPER_MODEL=tiny` for faster loading.

### YouTube Download Fails
**Solution**: Update yt-dlp: `pip install --upgrade yt-dlp`

### CORS Issues (Frontend Integration)
CORS is already configured for common frontend development ports. If you need to add additional origins, update `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React
    'http://localhost:5173',  # Vite
    'http://localhost:8080',  # Vue
    'your-frontend-url-here',
]
```

## 🌐 Frontend Integration

This backend API is designed to work with the Quizly frontend application. 

### Frontend Repository
👉 **[Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)**

The frontend provides:
- 🎨 Modern user interface
- 📱 Responsive design
- ⚡ Real-time quiz interaction
- 🔐 Secure authentication flow
- 📊 Quiz results visualization

### Quick Start with Frontend

1. **Clone and start this backend** (follow Installation section above)
2. **Clone the frontend repository**:
   ```bash
   git clone https://github.com/Developer-Akademie-Backendkurs/project.Quizly
   cd project.Quizly
   ```
3. **Follow frontend setup instructions** in its README
4. **Both apps will communicate** via the configured CORS settings

The backend API runs on `http://localhost:8000` and the frontend typically runs on `http://localhost:3000` or `http://localhost:5173`.

## License

This project is for educational purposes.


