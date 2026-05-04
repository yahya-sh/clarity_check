import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent

# Should be changed in production env
SECRET_KEY = os.environ.get('SECRET_KEY', 'insecure-bc054a63d0f9c2b537d4b0f6bebadb3630dd73495a140241')

# If passed as env var should passed as integer in seconds
PERMANENT_SESSION_LIFETIME = os.environ.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=8))


SESSION_REFRESH_EACH_REQUEST = os.environ.get('SESSION_REFRESH_EACH_REQUEST', True)
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', False)
SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', True)
SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_PATH = os.environ.get('SESSION_COOKIE_PATH', '/')