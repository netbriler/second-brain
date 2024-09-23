"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

env = environ.Env()
environ.Env.read_env('./.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-#x0&n@5j7qk@r5vz4q!k@^4w^3j^9z@1@2$!8q@#&!7@z6&^@u')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INTERNAL_IPS = env.list(
    'INTERNAL_IPS',
    default=[
        '127.0.0.1',
    ],
)

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'livereload',
    'django.contrib.staticfiles',
    'corsheaders',
    'admin_auto_filters',
    'debug_toolbar',
    'django_celery_beat',
    'djangoql',
    'adminsortable2',
    'users',
    'telegram_bot',
    'courses',
    'ai',
    'reminders',
    'workflows',
]

if not DEBUG:
    INSTALLED_APPS.remove('debug_toolbar')
    INSTALLED_APPS.remove('livereload')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'livereload.middleware.LiveReloadScript',
    'users.middlewares.UserLanguageMiddleware',
]

if not DEBUG:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE.remove('livereload.middleware.LiveReloadScript')

X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ],
)
CSRF_TRUSTED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=[
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ],
)

ROOT_URLCONF = 'app.urls'

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

WSGI_APPLICATION = 'app.wsgi.application'
LANGUAGES = [
    ('en', '🇺🇸 English'),
    ('ru', '🇷🇺 Русский'),
    ('ua', '🇺🇦 Українська'),
]

LANGUAGE_CODE = 'ru-ru'

USE_I18N = True

USE_L10N = True

LOCALE_PATHS = [BASE_DIR / 'locale']
for path in LOCALE_PATHS:
    path.mkdir(parents=True, exist_ok=True)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': env('POSTGRES_HOST', default='localhost'),
        'PORT': env.int('POSTGRES_PORT', default=5432),
        'CONN_MAX_AGE': env.int('POSTGRES_CONN_MAX_AGE', default=30),
        'NAME': env('POSTGRES_NAME', default='postgres'),
        'USER': env('POSTGRES_USER', default='postgres'),
        'PASSWORD': env('POSTGRES_PASSWORD', default='postgres'),
        'OPTIONS': {
            'sslmode': env('POSTGRES_SSL_MODE', default='prefer'),
        },
    },
}

# Celery settings
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
BROKER_URL = CELERY_BROKER_URL
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

MEDIA_URL = 'media/'
MEDIA_ROOT = Path(BASE_DIR) / 'media'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = Path(BASE_DIR) / 'static'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

# Telegram bot settings
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_API_ID = env.int('TELEGRAM_API_ID', default=0)
TELEGRAM_API_HASH = env('TELEGRAM_API_HASH', default='')

TELEGRAM_WEB_SERVER_HOST = env('TELEGRAM_WEB_SERVER_HOST', default='0.0.0.0')  # noqa
TELEGRAM_WEB_SERVER_PORT = env.int('TELEGRAM_WEB_SERVER_PORT', default=8000)

TELEGRAM_WEBHOOK_PATH = env('TELEGRAM_WEBHOOK_PATH', default='/webhook')
TELEGRAM_WEBHOOK_SECRET = env('TELEGRAM_WEBHOOK_SECRET', default='')
TELEGRAM_BASE_WEBHOOK_URL = env('TELEGRAM_BASE_WEBHOOK_URL', default='')

GOOGLE_GEMINI_API_KEYS = env('GOOGLE_GEMINI_API_KEYS', default='').split(',')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
