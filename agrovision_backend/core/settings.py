"""
Django settings for core project.

Configuración preparada para:
- Desarrollo local
- PostgreSQL
- Cloudinary
- Frontend separado
- Despliegue del backend en Vercel
"""

import os
from pathlib import Path

import cloudinary
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# En desarrollo carga agrovision_backend/.env.
# En Vercel las variables se obtienen del entorno.
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """
    Convierte una variable de entorno a booleano.
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_list(name, default=""):
    """
    Convierte una variable separada por comas en una lista.
    """
    value = os.environ.get(name, default)

    return [
        item.strip().rstrip("/")
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# SEGURIDAD
# ============================================================

DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-only"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY es obligatorio en producción."
        )


# ============================================================
# HOSTS
# ============================================================

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver",
)

# Permite los dominios de despliegue de Vercel.
if ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")

# Vercel proporciona automáticamente la URL del deployment.
VERCEL_URL = os.environ.get("VERCEL_URL")

if VERCEL_URL:
    vercel_host = (
        VERCEL_URL
        .replace("https://", "")
        .replace("http://", "")
        .rstrip("/")
    )

    if vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_host)


# ============================================================
# APLICACIONES
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",

    "authtoken",
    "cultivos",
    "lotes",
    "metricas",
    "archivos",
    "ml_models",
    "ubicaciones",
    "repository",
    "geolocation",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Archivos estáticos
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS debe ejecutarse antes de CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URLS / WSGI
# ============================================================

ROOT_URLCONF = "core.urls"

WSGI_APPLICATION = "core.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# BASE DE DATOS
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL")


if DATABASE_URL:

    # Producción / Vercel
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

else:

    # Desarrollo local mediante variables PostgreSQL.
    REQUIRED_DB_VARS = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]

    missing_db_vars = [
        variable
        for variable in REQUIRED_DB_VARS
        if not os.environ.get(variable)
    ]

    if missing_db_vars:
        raise ImproperlyConfigured(
            "Faltan variables de PostgreSQL: "
            + ", ".join(missing_db_vars)
        )

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",

            "NAME": os.environ.get("POSTGRES_DB"),

            "USER": os.environ.get("POSTGRES_USER"),

            "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),

            "HOST": os.environ.get(
                "POSTGRES_HOST",
                "localhost",
            ),

            "PORT": os.environ.get(
                "POSTGRES_PORT",
                "5432",
            ),
        }
    }


# ============================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation."
        "CommonPasswordValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation."
        "NumericPasswordValidator",
    },
]


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = "es-co"

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


STORAGES = {
    "default": {
        "BACKEND":
        "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
        "whitenoise.storage."
        "CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# MACHINE LEARNING
# ============================================================

ML_CHECKPOINTS_DIR = (
    BASE_DIR
    / "ml_models"
    / "checkpoints"
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "",
).rstrip("/")


# ============================================================
# CORS
# ============================================================

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    ),
)

if (
    FRONTEND_URL
    and FRONTEND_URL not in CORS_ALLOWED_ORIGINS
):
    CORS_ALLOWED_ORIGINS.append(
        FRONTEND_URL
    )


# La autenticación utiliza cookies de sesión.
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# LOGIN
# ============================================================

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"


# ============================================================
# SESIONES
# ============================================================

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7


# Desarrollo local:
# SameSite=Lax
#
# Producción:
# frontend y backend se despliegan como servicios separados,
# por lo que se permite el envío de la cookie mediante HTTPS.

SESSION_COOKIE_SAMESITE = (
    "Lax"
    if DEBUG
    else "None"
)


# ============================================================
# CSRF
# ============================================================

CSRF_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SAMESITE = (
    "Lax"
    if DEBUG
    else "None"
)

CSRF_COOKIE_HTTPONLY = False


CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    ),
)


if (
    FRONTEND_URL
    and FRONTEND_URL not in CSRF_TRUSTED_ORIGINS
):
    CSRF_TRUSTED_ORIGINS.append(
        FRONTEND_URL
    )


BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "",
).rstrip("/")


if (
    BACKEND_URL
    and BACKEND_URL not in CSRF_TRUSTED_ORIGINS
):
    CSRF_TRUSTED_ORIGINS.append(
        BACKEND_URL
    )


# ============================================================
# HTTPS / PROXY
# ============================================================

# Vercel utiliza un proxy delante de Django.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    False,
)


# ============================================================
# SEGURIDAD ADICIONAL EN PRODUCCIÓN
# ============================================================

if not DEBUG:

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"

    SECURE_REFERRER_POLICY = (
        "strict-origin-when-cross-origin"
    )


# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_CLOUD_NAME = os.environ.get(
    "CLOUDINARY_CLOUD_NAME",
    "",
)

CLOUDINARY_API_KEY = os.environ.get(
    "CLOUDINARY_API_KEY",
    "",
)

CLOUDINARY_API_SECRET = os.environ.get(
    "CLOUDINARY_API_SECRET",
    "",
)


# Carpeta de fallback.
CLOUDINARY_FOLDER = (
    os.environ.get(
        "CLOUDINARY_DEFAULT_FOLDER"
    )
    or os.environ.get(
        "CLOUDINARY_FOLDER",
        "agrovision",
    )
)


# ============================================================
# CIFRADO DE CREDENCIALES DEL REPOSITORIO
# ============================================================

REPOSITORY_ENCRYPTION_KEY = os.environ.get(
    "REPOSITORY_ENCRYPTION_KEY",
    "",
)


# ============================================================
# GEOLOCALIZACIÓN
# ============================================================

NOMINATIM_BASE_URL = os.environ.get(
    "NOMINATIM_BASE_URL",
    "https://nominatim.openstreetmap.org",
)

NOMINATIM_USER_AGENT = os.environ.get(
    "NOMINATIM_USER_AGENT",
    "AgriVisionOS/1.0 (+https://github.com/agrovision)",
)


# ============================================================
# CONFIGURACIÓN CLOUDINARY
# ============================================================

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)