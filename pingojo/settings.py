import os
from pathlib import Path
import socket
import dj_database_url
import sentry_sdk
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from sentry_sdk.integrations.django import DjangoIntegration

if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN','sentry_dsn'),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=True
    )

SECRET_KEY = os.environ.get('SECRET_KEY','secret')
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = ['www.pingojo.com','127.0.0.1', os.environ.get('RENDER_EXTERNAL_HOSTNAME','localhost'), 'localhost']
ALLOWED_HOSTS.append(socket.getaddrinfo(socket.gethostname(), 'http')[0][4][0])

if 'CODESPACE_NAME' in os.environ:
    ALLOWED_HOSTS.append('localhost')
    codespace_name = os.getenv("CODESPACE_NAME")
    codespace_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    CSRF_TRUSTED_ORIGINS = [f'https://{codespace_name}-8000.{codespace_domain}']
    ALLOWED_HOSTS.append(f'https://{codespace_name}-8000.{codespace_domain}')


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "website",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "corsheaders",
    'debug_toolbar',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", 
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    #"website.middleware.CustomMiddleware",    
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': './django_cache_directory',
    }
}


CORS_ALLOWED_ORIGINS = [
    "https://mail.google.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://boards.greenhouse.io",
    "https://boards.eu.greenhouse.io",
    "https://wellfound.com",
    # Add any other allowed origins
]

def show_toolbar(request):
    return request.user.is_superuser

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
}

ENABLE_DEBUG_TOOLBAR = os.environ.get('ENABLE_DEBUG_TOOLBAR',True)

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SAMESITE = 'None'

CORS_ALLOW_CREDENTIALS = True

#SESSION_COOKIE_SAMESITE = None
#CSRF_COOKIE_SAMESITE = None

#CORS_ALLOW_ALL_ORIGINS = True

CORS_ORIGIN_ALLOW_ALL = False
CSRF_TRUSTED_ORIGINS = [
    "https://mail.google.com","https://boards.greenhouse.io", "https://wellfound.com", "https://boards.eu.greenhouse.io"]

CORS_ORIGIN_WHITELIST = [
    'https://mail.google.com',
    'https://boards.greenhouse.io',
    'https://boards.eu.greenhouse.io',
    'https://wellfound.com',
]

ROOT_URLCONF = "pingojo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "pingojo.wsgi.application"

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'pingojo',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL',''))
    }
if os.environ.get('DATABASE_URL',''):
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL',''))
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1
LOGIN_REDIRECT_URL = "/"

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_FORMS = {
    'signup': 'website.forms.CustomSignupForm',
}
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 100000000

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)
# used for generating unique urls that can't be guessed
HASHID_FIELD_SALT = (os.environ.get("HASHID_FIELD_SALT","salt123"))


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY","your_sendgrid_api_key")
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER","apikey")
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL","email@server.com")

SLACK_WEBHOOK_URL =  os.environ.get("SLACK_WEBHOOK_URL","your_slack_webhook_url")
ACCOUNT_LOGOUT_CONFIRMATION = False
ACCOUNT_LOGOUT_ON_GET = True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}



import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'django': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOG_LEVEL', 'ERROR'),
        'propagate': False,
    },
}