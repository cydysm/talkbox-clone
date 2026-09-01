"""请求相关的通用小工具。"""

from django.conf import settings


def get_client_ip(request) -> str:
    """限流/记录用的客户端 IP。

    默认取 REMOTE_ADDR（直连部署下唯一可信）；部署在可信反代之后时打开
    USE_X_FORWARDED_FOR，取 X-Forwarded-For 的最左值。开这个开关的前提是
    反代会覆盖（而非追加）该头，否则客户端可伪造 IP 绕过限流。
    """
    if getattr(settings, "USE_X_FORWARDED_FOR", False):
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.META.get("REMOTE_ADDR") or "unknown"
