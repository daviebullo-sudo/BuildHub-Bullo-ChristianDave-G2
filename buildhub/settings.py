"""Django settings for the BuildHub project."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Secrets and database credentials live in .env (never committed to Git).
load_dotenv(BASE_DIR / '.env')


def get_env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(
            f'Missing required environment variable: {name}. Add it to your .env file.'
        )
    return value


SECRET_KEY = get_env('DJANGO_SECRET_KEY', required=True)
DEBUG = get_env('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [
    host.strip()
    for host in get_env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'projects',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'buildhub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'buildhub.wsgi.application'

# Set USE_SQLITE=True in .env to run locally without PostgreSQL (development only).
# The final submission must use PostgreSQL / Supabase, so set USE_SQLITE=False then.
USE_SQLITE = get_env('USE_SQLITE', 'False').lower() == 'true'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # PostgreSQL / Supabase (Supabase is PostgreSQL).
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_env('DB_NAME', required=True),
            'USER': get_env('DB_USER', required=True),
            'PASSWORD': get_env('DB_PASSWORD', required=True),
            'HOST': get_env('DB_HOST', 'localhost'),
            'PORT': get_env('DB_PORT', '5432'),
            'OPTIONS': {'sslmode': get_env('DB_SSLMODE', 'prefer')},
        }
    }

# Custom user model (adds role, contact number, profile photo).
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
