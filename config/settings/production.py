import sys

from django.core.exceptions import ImproperlyConfigured

from .base import *


def validate_production_security(secret_key, allowed_hosts):
    if not secret_key or secret_key == "insecure-change-me" or len(secret_key) < 32:
        raise ImproperlyConfigured(
            "SECRET_KEY 必须设置为至少 32 个字符的随机值，不能使用默认值。"
        )
    if not allowed_hosts or "*" in allowed_hosts:
        raise ImproperlyConfigured("ALLOWED_HOSTS 必须显式配置，不能为空或使用通配符。")


if "test" not in sys.argv:
    validate_production_security(SECRET_KEY, ALLOWED_HOSTS)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "strict-origin-when-cross-origin"
