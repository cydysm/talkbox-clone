from .base import *

DEBUG = env.bool("DEBUG", default=True)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "talkbox-local",
    }
}

if DEBUG:
    ALLOWED_HOSTS = ["*"]
