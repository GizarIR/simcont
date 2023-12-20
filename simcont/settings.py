"""
Django settings for simcont project.

Generated by 'django-admin startproject' using Django 4.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import logging
import os
from datetime import timedelta
from pathlib import Path

from decouple import config

# Read .env
DJANGO_ENV = config('DJANGO_ENV')
SECRET_KEY_PRJ = config('SECRET_KEY_PRJ')

TOKEN_LIFE_MINUTES = config('TOKEN_LIFE_MINUTES')
TOKEN_REFRESH_DAYS = config('TOKEN_REFRESH_DAYS')

DATABASE_HOSTNAME = config('DEFAULT_DATABASE_HOSTNAME')
DATABASE_DB = config("DEFAULT_DATABASE_DB")
DATABASE_USER = config("DEFAULT_DATABASE_USER")
DATABASE_PASSWORD = config("DEFAULT_DATABASE_PASSWORD")
DATABASE_PORT = config("DEFAULT_DATABASE_PORT")

NLP_MAX_LENGTH = config('NLP_MAX_LENGTH')
DEFAULT_TRANSLATE_STRATEGY = config('DEFAULT_TRANSLATE_STRATEGY')
OPENAI_API_KEY = config('OPENAI_API_KEY')

REDIS_PORT = config('REDIS_PORT')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY_PRJ

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DJANGO_ENV == 'DEV'

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'rest_framework',
    'drf_yasg',  # https://drf-yasg.readthedocs.io/en/stable/index.html
    'users.apps.UsersConfig',
    'drf_app.apps.Drf_appConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'simcont.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'drf_app/templates/drf_app/')],
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

WSGI_APPLICATION = 'simcont.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DATABASE_DB,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOSTNAME,
        'PORT': DATABASE_PORT,
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ******** For debug tool django-debug-toolbar ***************
INTERNAL_IPS = [
    '127.0.0.1',
]
# ******** End debug tool django-debug-toolbar block *********


# **************Setting for Auth by Email:********************
# https://medium.com/@therealak12/authenticate-using-email-instead-of-username-in-django-rest-framework-857645037bab


# For Customer default user model
AUTH_USER_MODEL = 'users.CustomUser'

# For tell Django to use this backend as the default authentication backend.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'users.auth_backends.EmailBackend',
]
# ************* End Auth by Email Block*************************

# ***************** REST Framework *****************
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication' if DJANGO_ENV == 'DEV' else None,
        'rest_framework.authentication.BasicAuthentication' if DJANGO_ENV == 'DEV' else None,
        'rest_framework.authentication.SessionAuthentication' if DJANGO_ENV == 'DEV' else None,
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DJANGO_ENV == 'DEV' else None,  # On/Off DRF interface
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 5,
}
# ***************** END DRF *****************


# ************* Load Images*************************
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
# ************* End Load Images*************************


# ************* Auth settint SimpleJWT *************************
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(TOKEN_LIFE_MINUTES)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(TOKEN_REFRESH_DAYS)),
}
# ************* END SimpleJWT *************************

# ************* Swagger Setting  drf-yasg*************************
SWAGGER_SETTINGS = {"DEFAULT_AUTO_SCHEMA_CLASS": "drf_app.views.CustomAutoSchema"}  # For group endpoints by ViewSets
# ************* END Swagger*************************

# ************* Celery *************************
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = 'UTC'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# ************* END Celery *************************

# ************* Logging *************************
# LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGING_LEVEL = logging.INFO

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/file.log',
        },
    },
    'root': {
        'handlers': ['console' if DEBUG else 'file'],
        'level': LOGGING_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console' if DEBUG else 'file'],
            'level': LOGGING_LEVEL,
            'propagate': True,
        },
    },
}
# ************* END Logging *************************

# ************* Any*************************
# ************* END Any *************************

# ************* Any*************************
# ************* END Any *************************
