import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.users',
    'apps.catalog',
    'apps.courses',
    'apps.orders',
    'apps.payments',
    'apps.wallet',
    'apps.favorites',
    'apps.bot_messages',
    'apps.settings_app',
    'apps.telegram_bot',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
_db_url = config('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/medcardy')
_db_parts = _db_url.replace('postgres://', '').replace('postgresql://', '')
_user_pass, _rest = _db_parts.split('@')
_user, _password = _user_pass.split(':')
_host_port_db = _rest.split('/')
_db_name = _host_port_db[1]
_host_port = _host_port_db[0].split(':')
_host = _host_port[0]
_port = _host_port[1] if len(_host_port) > 1 else '5432'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _db_name,
        'USER': _user,
        'PASSWORD': _password,
        'HOST': _host,
        'PORT': _port,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram Bot
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_BOT_USERNAME = config('TELEGRAM_BOT_USERNAME', default='MedCardyBot')

# Site
SITE_BASE_URL = config('SITE_BASE_URL', default='http://localhost:8000')

# Zibal
ZIBAL_BASE_URL = config('ZIBAL_BASE_URL', default='https://gateway.zibal.ir')
ZIBAL_MERCHANT = config('ZIBAL_MERCHANT', default='zibal')
ZIBAL_CALLBACK_URL = config('ZIBAL_CALLBACK_URL', default='http://localhost:8000/api/payments/zibal/callback/')
ZIBAL_TEST_MODE = config('ZIBAL_TEST_MODE', default=True, cast=bool)

# Support
DEFAULT_SUPPORT_USERNAME = config('DEFAULT_SUPPORT_USERNAME', default='@MedCardySupport')

# Telegram admin panel (comma-separated numeric Telegram user IDs)
ADMIN_TELEGRAM_IDS = config('ADMIN_TELEGRAM_IDS', default='', cast=Csv(int))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
