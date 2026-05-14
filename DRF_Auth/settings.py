
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=None):
    value = os.getenv(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(',') if item.strip()]


def env_int(name, default):
    return int(os.getenv(name, default))





# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-change-this-local-development-key'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DEBUG', True)

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', ['localhost', '127.0.0.1'])

CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS',['http://localhost:3000','http://127.0.0.1:3000',])




SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', False)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', False)
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', 0)



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders', # CORS
    # 'Authentication',
    'Authentication.apps.AuthenticationConfig',
    'drf_spectacular', #swagger

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', #whitenoise
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

ROOT_URLCONF = 'DRF_Auth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DRF_Auth.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv('DB_NAME', 'postgres'),
#         "USER": os.getenv('DB_USER', 'postgres'),
#         "PASSWORD": os.getenv('DB_PASSWORD', 'postgres'),
#         "HOST": os.getenv('DB_HOST', 'localhost'),
#         "PORT": os.getenv('DB_PORT', '5432'),
#     }
# }

# DB_SCHEMA = os.getenv('DB_SCHEMA')
# if DB_SCHEMA:
#     DATABASES['default']['OPTIONS'] = {
#         'options': f'-c search_path={DB_SCHEMA}'
#     }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

#Whitenoise storage
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = ''
# LOGIN_URL = '/login/'

AUTH_USER_MODEL = 'Authentication.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'Authentication.authentication.SessionJWTAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    'DEFAULT_THROTTLE_RATES': {
        'login': '10/hour',
        'verification': '10/hour',
        'register': '10/hour',
        'password-reset': '10/hour',
    },

    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', # swagger


}

# swagger
SPECTACULAR_SETTINGS = {
    'TITLE': 'DRF Custom Auth API',
    'DESCRIPTION': 'Auto-generated API schema for DRF Custom Auth',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'SECURITY_SCHEMES': {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }
    },
}


SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=1500),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
}





EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = env_int('EMAIL_PORT', 587)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = env_int('EMAIL_TIMEOUT', 60)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'hasibsorker02@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'xxx-xxx-xxx')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'hasibsorker02@gmail.com')




# Frontend URL for email sending verifications links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


PASSWORD_RESET_TIMEOUT = env_int('PASSWORD_RESET_TIMEOUT', 600)
OTP_EXPIRE_TIMEOUT = env_int('OTP_EXPIRE_TIMEOUT', 600)
MAX_WRONG_OTP_ATTEMPTS = env_int('MAX_WRONG_OTP_ATTEMPTS', 5)
OTP_LOCKED_UNTIL = env_int('OTP_LOCKED_UNTIL', 600)
MAX_LOGIN_ATTEMPTS = env_int('MAX_LOGIN_ATTEMPTS', 5)
ACCOUNT_LOCKOUT_DURATION = env_int('ACCOUNT_LOCKOUT_DURATION', 600)

GEOLOCATION_ENABLED = env_bool('GEOLOCATION_ENABLED', True)
GEOLOCATION_TIMEOUT = env_int('GEOLOCATION_TIMEOUT', 3)

LOGIN_HISTORY_RETENTION_DAYS = env_int('LOGIN_HISTORY_RETENTION_DAYS', 90)
INACTIVE_SESSION_RETENTION_DAYS = env_int('INACTIVE_SESSION_RETENTION_DAYS', 30)
TWO_FA_LOG_RETENTION_DAYS = env_int('TWO_FA_LOG_RETENTION_DAYS', 30)



