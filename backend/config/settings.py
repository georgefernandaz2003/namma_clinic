import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION & VALIDATION
# -----------------------------------------------------------------------------
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'local').strip().lower()
if DJANGO_ENV not in ('local', 'staging', 'production'):
    raise ImproperlyConfigured(
        f"Invalid DJANGO_ENV: '{DJANGO_ENV}'. Must be one of: 'local', 'staging', 'production'."
    )

# DEBUG
if DJANGO_ENV == 'production':
    raw_debug = os.environ.get('DJANGO_DEBUG', 'False').strip().lower()
    if raw_debug in ('true', '1'):
        raise ImproperlyConfigured(
            "In production, DJANGO_DEBUG must be False. Running with DEBUG=True in production is strictly forbidden."
        )
    DEBUG = False
elif DJANGO_ENV == 'staging':
    DEBUG = os.environ.get('DJANGO_DEBUG', 'False').strip().lower() in ('true', '1')
else:  # local
    DEBUG = os.environ.get('DJANGO_DEBUG', 'True').strip().lower() in ('true', '1')

# SECRET_KEY
DEMO_SECRET_KEY = 'django-insecure-namma-clinic-digital-health-platform-key-demo-only'
env_secret_key = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')

if DJANGO_ENV == 'production':
    if not env_secret_key or env_secret_key == DEMO_SECRET_KEY:
        raise ImproperlyConfigured(
            "In production, DJANGO_SECRET_KEY must be provided from the environment and cannot be the default demo key."
        )
    SECRET_KEY = env_secret_key
elif DJANGO_ENV == 'staging':
    SECRET_KEY = env_secret_key or 'django-staging-namma-clinic-key-for-testing-only'
else:  # local
    SECRET_KEY = env_secret_key or DEMO_SECRET_KEY

# ALLOWED_HOSTS
env_allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS')

if DJANGO_ENV == 'production':
    if not env_allowed_hosts:
        raise ImproperlyConfigured(
            "In production, DJANGO_ALLOWED_HOSTS must be explicitly defined as a comma-separated list of hostnames."
        )
    ALLOWED_HOSTS = [h.strip() for h in env_allowed_hosts.split(',') if h.strip()]
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "In production, DJANGO_ALLOWED_HOSTS cannot be empty or contain wildcard '*'."
        )
elif DJANGO_ENV == 'staging':
    if env_allowed_hosts:
        ALLOWED_HOSTS = [h.strip() for h in env_allowed_hosts.split(',') if h.strip()]
    else:
        ALLOWED_HOSTS = ['staging.nammaclinic.in', 'localhost', '127.0.0.1']
else:  # local
    if env_allowed_hosts:
        ALLOWED_HOSTS = [h.strip() for h in env_allowed_hosts.split(',') if h.strip()]
    else:
        ALLOWED_HOSTS = ['*']

# -----------------------------------------------------------------------------
# 2. APPLICATIONS & MIDDLEWARE
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local apps
    'apps.accounts',
    'apps.geography',
    'apps.facilities',
    'apps.patients',
    'apps.visits',
    'apps.triage',
    'apps.consultations',
    'apps.laboratory',
    'apps.pharmacy',
    'apps.referrals',
    'apps.ncd',
    'apps.surveillance',
    'apps.telemedicine',
    'apps.outreach',
    'apps.wellness',
    'apps.ars',
    'apps.quality',
    'apps.reports',
    'apps.alerts',
    'apps.integrations',
    'apps.compliance',
    'apps.audit',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# -----------------------------------------------------------------------------
# 3. DATABASE CONFIGURATION (LOCAL LAPTOP TARGET: POSTGRESQL 16)
# -----------------------------------------------------------------------------
DB_ENGINE = os.environ.get('DATABASE_ENGINE', '').strip().lower()

if DJANGO_ENV == 'production':
    if not DB_ENGINE or 'postgresql' not in DB_ENGINE:
        raise ImproperlyConfigured(
            "In production, DATABASE_ENGINE must be 'django.db.backends.postgresql'. SQLite is strictly prohibited."
        )
    db_name = os.environ.get('DATABASE_NAME')
    db_user = os.environ.get('DATABASE_USER')
    db_password = os.environ.get('DATABASE_PASSWORD')
    db_host = os.environ.get('DATABASE_HOST')
    db_port = os.environ.get('DATABASE_PORT', '5432')
    if not (db_name and db_user and db_password and db_host):
        raise ImproperlyConfigured(
            "In production, complete PostgreSQL connection parameters "
            "(DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST) are mandatory."
        )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
            'CONN_MAX_AGE': int(os.environ.get('DATABASE_CONN_MAX_AGE', '60')),
        }
    }
elif DJANGO_ENV == 'staging':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DATABASE_NAME', 'namma_clinic_staging'),
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DATABASE_CONN_MAX_AGE', '0')),
            'TEST': {
                'NAME': os.environ.get('DATABASE_TEST_NAME', 'test_namma_clinic_staging'),
            },
        }
    }
else:
    # LOCAL (Default target: Native local PostgreSQL 16 on laptop)
    if 'sqlite' in DB_ENGINE:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        # Resolve active local PostgreSQL port (supports dynamic pgserver or standard 5432)
        local_port = os.environ.get('DATABASE_PORT')
        if not local_port:
            try:
                from pgserver.utils import PostmasterInfo
                pinfo = PostmasterInfo.read_from_pgdata(BASE_DIR.parent / 'pgdata')
                if pinfo and pinfo.is_running():
                    local_port = str(pinfo.port)
            except Exception:
                pass
        local_port = local_port or '5432'

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DATABASE_NAME', 'namma_clinic_local'),
                'USER': os.environ.get('DATABASE_USER', 'postgres'),
                'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
                'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
                'PORT': local_port,
                'CONN_MAX_AGE': int(os.environ.get('DATABASE_CONN_MAX_AGE', '0')),
                'TEST': {
                    'NAME': os.environ.get('DATABASE_TEST_NAME', 'test_namma_clinic_local'),
                },
            }
        }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# -----------------------------------------------------------------------------
# 4. PASSWORD VALIDATION
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# -----------------------------------------------------------------------------
# 5. SECURITY & HTTP HARDENING
# -----------------------------------------------------------------------------
if DJANGO_ENV == 'production':
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').strip().lower() in ('true', '1')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').strip().lower() in ('true', '1')
    SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'True').strip().lower() in ('true', '1')
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
elif DJANGO_ENV == 'staging':
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').strip().lower() in ('true', '1')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').strip().lower() in ('true', '1')
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
else:  # local
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    SECURE_BROWSER_XSS_FILTER = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# -----------------------------------------------------------------------------
# 6. STATIC & MEDIA FILES
# -----------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# 7. CORS CONFIGURATION
# -----------------------------------------------------------------------------
env_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()

if DJANGO_ENV == 'production':
    CORS_ALLOW_ALL_ORIGINS = False
    if env_cors_origins:
        CORS_ALLOWED_ORIGINS = [o.strip() for o in env_cors_origins.split(',') if o.strip()]
    else:
        CORS_ALLOWED_ORIGINS = []
elif DJANGO_ENV == 'staging':
    CORS_ALLOW_ALL_ORIGINS = False
    if env_cors_origins:
        CORS_ALLOWED_ORIGINS = [o.strip() for o in env_cors_origins.split(',') if o.strip()]
    else:
        CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
else:  # local
    CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').strip().lower() in ('true', '1')
    if env_cors_origins:
        CORS_ALLOWED_ORIGINS = [o.strip() for o in env_cors_origins.split(',') if o.strip()]
    else:
        CORS_ALLOWED_ORIGINS = []

# -----------------------------------------------------------------------------
# 8. REST FRAMEWORK & JWT
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'apps.common.api_exceptions.domain_exception_handler',
}

# Environment-driven JWT token configuration
# Defaults preserve full backward compatibility with development/test baselines.
JWT_ACCESS_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_MINUTES', '10080'))  # Default: 7 days
JWT_REFRESH_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_DAYS', '30'))        # Default: 30 days

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=JWT_REFRESH_DAYS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# -----------------------------------------------------------------------------
# 9. STRUCTURED LOGGING FOUNDATION
# -----------------------------------------------------------------------------
LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '[%(asctime)s] [%(levelname)s] [%(process)d:%(thread)d] [%(name)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
