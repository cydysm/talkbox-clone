from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.http import HttpResponseForbidden

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300


class RateLimitedLoginView(auth_views.LoginView):
    """Block IPs after repeated failed admin login attempts."""

    template_name = "admin/login.html"

    def dispatch(self, request, *args, **kwargs):
        client_ip = request.META.get("REMOTE_ADDR") or "unknown"
        key = f"login-fail:{client_ip}"

        if request.method == "POST":
            failures = cache.get(key, 0)
            if failures >= LOGIN_RATE_LIMIT:
                return HttpResponseForbidden(
                    "登录失败次数过多，请 5 分钟后再试。"
                )

        response = super().dispatch(request, *args, **kwargs)

        if request.method == "POST" and response.status_code == 200:
            cache.set(key, cache.get(key, 0) + 1, LOGIN_RATE_WINDOW)
        elif request.method == "POST" and response.status_code in (302, 303):
            cache.delete(key)

        return response
