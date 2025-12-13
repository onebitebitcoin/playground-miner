import os
from pathlib import Path
from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root (two levels up from settings.py)
env_path = BASE_DIR.parent / '.env'
# Decouple Config always requires a repository; fall back to an empty mapping
# so production environments without a .env still work via os.environ.
config = Config(RepositoryEnv(env_path)) if env_path.exists() else Config({})

# Load environment variables
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Comma-separated list of origins allowed to call APIs from the browser.
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in config(
        'CORS_ALLOWED_ORIGINS',
        default=(
            'http://localhost:3000,'
            'http://localhost:5173,'
            'http://localhost:6173,'
            'http://127.0.0.1:3000,'
            'http://127.0.0.1:5173,'
            'http://127.0.0.1:6173'
        )
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blocks.apps.BlocksConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'playground_server.simplecors.CORSMiddleware',
]

ROOT_URLCONF = 'playground_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'playground_server.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Persistent DB connections to reduce cold-connection latency
CONN_MAX_AGE = 60

# OpenAI configuration for finance insights
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
OPENAI_API_BASE = config('OPENAI_API_BASE', default='https://api.openai.com/v1')
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4o-mini')
ECOS_API_KEY = config('ECOS_API_KEY', default='')

# FRED API for M2 Money Supply data
FRED_API_KEY = config('FRED_API_KEY', default='')

# Note: No global caching configured to avoid stale heights on real-time UI

# Logging configuration for encryption operations
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',
        },
        'backend_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'backend.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'backend': {
            'handlers': ['backend_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'blocks.encryption': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'blocks.models': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'blocks.views': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
