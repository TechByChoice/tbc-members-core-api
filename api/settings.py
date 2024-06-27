"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path
import logging.config
import logging

from celery.schedules import crontab
from corsheaders.middleware import CorsMiddleware
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, ".env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    ALLOWED_HOSTS = [
        "beta-api.techbychoice.org",
        "beta-api-dev.techbychoice.org"
    ]
    # ALLOWED_HOSTS = [
    #     "localhost",
    #     "127.0.0.1"
    # ]
    # CSRF_TRUSTED_ORIGINS = [
    #     "http://localhost:3000",
    #     "http://localhost:8003",
    #     "http://localhost:7000"
    # ]
else:
    ALLOWED_HOSTS = [
        "beta-api.techbychoice.org",
        "beta-api-dev.techbychoice.org"
    ]
# CSRF_TRUSTED_ORIGINS = [
#     "https://www.beta.techbychoice.org",
#     "https://beta.techbychoice.org",
#     "https://www.opendoors.api.techbychoice.org",
#     "https://opendoors.api.techbychoice.org",
# ]
# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "knox",
    "apps.core",
    "apps.company",
    "apps.member",
    "apps.mentorship",
    "corsheaders",
    "storages",
    "django_filters"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # cross domain
    "corsheaders.middleware.CorsMiddleware",
    # "api.restrict_origin_middleware.RestrictOriginMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # firewall
    # "apps.core.firewall_middleware.FirewallMiddleware",
    # CORS Rules
]

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, 'apps/core/templates')
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("PGDATABASE"),
        "USER": os.getenv("PGUSER"),
        "PASSWORD": os.getenv("PGPASSWORD"),
        "HOST": os.getenv("PGHOST"),
        "PORT": os.getenv("PGPORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

USE_S3 = os.getenv("USE_S3") == "TRUE"

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # s3 static settings
    STATIC_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    # s3 public media settings
    PUBLIC_MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "api.storage_backends.PublicMediaStorage"
    # s3 private media settings
    PRIVATE_MEDIA_LOCATION = "private"
    PRIVATE_FILE_STORAGE = "api.storage_backends.PrivateMediaStorage"
else:
    STATIC_URL = "/staticfiles/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    MEDIA_URL = "/mediafiles/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Adding details for auth token from knox
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "knox.auth.TokenAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.UserRateThrottle',
    #     'rest_framework.throttling.AnonRateThrottle',
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'user': '10/minute',
    #     'anon': '5/minute',
    # }
}

# Security settings

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "https://www.beta.techbychoice.org",
        "https://beta.techbychoice.org",
        "https://www.dev.techbychoice.org",
        "https://dev.techbychoice.org",
        "https://www.opendoors-api-dev.techbychoice.org",
        "https://opendoors-api-dev.techbychoice.org",
        "https://www.opendoors-api.techbychoice.org",
        "https://opendoors-api.techbychoice.org",
        "https://www.internal-dev-api.techbychoice.org",
        "https://internal-dev-api.techbychoice.org",
        "https://www.internal-api.techbychoice.org",
        "https://internal-api.techbychoice.org",
    ]
    # CORS_ALLOWED_ORIGINS = [
    #     "http://localhost:3000",
    #     "http://localhost:8003",
    #     "http://localhost:7000",
    # ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://www.beta.techbychoice.org",
        "https://beta.techbychoice.org",
        "https://www.dev.techbychoice.org",
        "https://dev.techbychoice.org",
        "https://www.opendoors-api-dev.techbychoice.org",
        "https://opendoors-api-dev.techbychoice.org",
        "https://www.opendoors-api.techbychoice.org",
        "https://opendoors-api.techbychoice.org",
        "https://www.internal-dev-api.techbychoice.org",
        "https://internal-dev-api.techbychoice.org",
        "https://www.internal-api.techbychoice.org",
        "https://internal-api.techbychoice.org",
    ]

# Allow cookies
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        'level': 'INFO'
    },
}

# Celery workflow
# Celery Configuration Options
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
# Celery Broker - Redis
# CELERY_BROKER_URL = os.getenv("REDIS_URL")
# CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")
CELERY_REDIS_DB = '0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_DEFAULT_QUEUE = 'core-api'

# Celery Schedule
CELERY_BEAT_SCHEDULECELERY_BEAT_SCHEDULE = {
    # "run-my-task-every-day-at-9am": {
    #     "task": "job.tasks.daily_talent_choice_new_company_account_request_reminder",
    #     "schedule": crontab(hour=9, minute=0, day_of_week="mon-fri"),
    # },
    "close-old-jobs": {
        "task": "apps.company.tasks.close_old_jobs",
        "schedule": crontab(hour=9, minute=0, day_of_week="mon-fri"),
        # "schedule": crontab(minute='*/1'),
    },
}

# Redis

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "core-api",
    }
}

AUTH_USER_MODEL = "core.CustomUser"

REST_KNOX = {
    "TOKEN_TTL": timedelta(days=14),
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# JWT TOKEN
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION = timedelta(days=7)

# Ensure you don't run collectstatic during deployment if not necessary
DISABLE_COLLECTSTATIC = 1

# Email setting

EMAIL_BACKEND = 'apps.core.email_backends.SendGridPasswordResetEmailBackend'

CORS_EXPOSE_HEADERS = [
    'access-control-allow-origin',
    'content-type',
    'x-csrftoken',
]

logger = logging.getLogger(__name__)


class LoggingCorsMiddleware(CorsMiddleware):
    def process_request(self, request):
        response = super().process_request(request)
        logger.info(f"CORS request to {request.path} with origin {request.META.get('HTTP_ORIGIN')}")
        return response

