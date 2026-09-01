from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        marker = "healthz:probe"
        cache.set(marker, True, 5)
        checks["cache"] = "ok" if cache.get(marker) else "error"
        cache.delete(marker)
    except Exception:
        checks["cache"] = "error"

    healthy = all(value == "ok" for value in checks.values())
    # 紧凑分隔符：compose healthcheck 与 scripts/{upgrade,restore}.sh 都以
    # `"status":"ok"`（无空格）作为 grep 模式，默认的 `": "` 会匹配失败。
    return JsonResponse(
        {"status": "ok" if healthy else "error", "checks": checks},
        status=200 if healthy else 503,
        json_dumps_params={"separators": (",", ":")},
    )
