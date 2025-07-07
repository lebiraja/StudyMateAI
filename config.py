"""
Configuration settings for StudyMateAI
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR

# Data subdirectories
DOWNLOAD_DIRS = {
    'application/pdf': DATA_DIR / 'pdfs',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DATA_DIR / 'docs',
    'application/vnd.google-apps.document': DATA_DIR / 'docs',
    'video/mp4': DATA_DIR / 'materials',
    'image/jpeg': DATA_DIR / 'materials',
    'image/png': DATA_DIR / 'materials',
    'text/plain': DATA_DIR / 'assignments'
}

ASSIGNMENT_DIR = DATA_DIR / "assignments"
ASSIGNMENT_ANSWERS_DIR = DATA_DIR / "assignment_answers"
LOGS_DIR = BASE_DIR / "logs"

# File extensions mapping
EXTENSION_MAP = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.google-apps.document': '.docx',
    'video/mp4': '.mp4',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'text/plain': '.txt'
}

# Google API settings
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/drive.file'
]

# AI Model settings
EMBEDDING_MODEL = "bge-m3"
CHAT_MODEL = "llama3.2"  # Use a more common model
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_CONTEXT_CHUNKS = 3

# ChromaDB settings
CHROMA_COLLECTION_NAME = "studymate_enhanced"
CHROMA_PERSIST_DIRECTORY = str(DATA_DIR / "chroma_db")

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_ENCODING = "utf-8"

# Create directories if they don't exist
for dir_path in [DATA_DIR, ASSIGNMENT_ANSWERS_DIR, LOGS_DIR, *DOWNLOAD_DIRS.values()]:
    dir_path.mkdir(parents=True, exist_ok=True)

