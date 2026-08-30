from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "insecure-change-me"),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, "sqlite:///local.sqlite3"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    THEME=(str, "cactus_dark"),
    SITE_NAME=(str, "Talkbox"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "apps.blog.apps.TaggitChineseConfig",
    "apps.blog",
    "apps.comments",
    "apps.mediafiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                (
                    "apps.blog.theme_loader.ActiveThemeCachedLoader",
                    [
                        # filesystem.Loader 在最前，项目根 templates/ 可覆写 admin 模板
                        "django.template.loaders.filesystem.Loader",
                        "apps.blog.theme_loader.ActiveThemeFilesystemLoader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.blog.context.theme_context",
            ],
        },
    }
]

DATABASES = {"default": env.db_url("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Singapore"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
AVAILABLE_THEMES = [
    "cactus_dark",
    "cactus_light",
]
STATICFILES_DIRS = [
    BASE_DIR / "themes" / theme_name / "static"
    for theme_name in AVAILABLE_THEMES
]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
THEME = env("THEME")
PLUGIN_DIRS = [BASE_DIR / "plugins"]
import sys

for _plugin_dir in PLUGIN_DIRS:
    if str(_plugin_dir) not in sys.path:
        sys.path.insert(0, str(_plugin_dir))
SITE_NAME = env("SITE_NAME")
SITE_DESCRIPTION = env("SITE_DESCRIPTION", default="Talkbox Clone - Python blog")
FEED_LIMIT = env.int("FEED_LIMIT", default=20)
POSTS_PER_PAGE = env.int("POSTS_PER_PAGE", default=10)
NAV_MAX_ITEMS = env.int("NAV_MAX_ITEMS", default=8)

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")
NOTIFY_EMAIL = env("NOTIFY_EMAIL", default="")
COMMENT_REPLY_NOTIFY = env.bool("COMMENT_REPLY_NOTIFY", default=True)
COMMENT_INTERVAL_SECONDS = env.int("COMMENT_INTERVAL_SECONDS", default=30)
WATERMARK_TEXT = env("WATERMARK_TEXT", default="")
WATERMARK_IMAGE_PATH = env("WATERMARK_IMAGE_PATH", default="")
UPLOAD_MAX_BYTES = env.int("UPLOAD_MAX_MB", default=10) * 1024 * 1024
UPLOAD_MAX_IMAGES = env.int("UPLOAD_MAX_IMAGES", default=20)
UPLOAD_TOTAL_LIMIT_GB = env.int("UPLOAD_TOTAL_LIMIT_GB", default=20)
IMAGE_MAX_DIMENSION = env.int("IMAGE_MAX_DIMENSION", default=8000)
ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP", "GIF"]
THUMBNAIL_SIZE = env.tuple("THUMBNAIL_SIZE", default=(240, 240))

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "talkbox.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "talkbox": {"handlers": ["console", "app_file"], "level": "INFO"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}
