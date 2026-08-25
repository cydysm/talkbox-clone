from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "talkbox-local",
    }
}
