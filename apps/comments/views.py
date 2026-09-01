import sys
import threading

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import connections
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from config.request_utils import get_client_ip

from .forms import CommentForm
from .notifications import send_comment_notification


def _is_test_environment():
    return "test" in sys.argv


def _safe_next_url(request) -> str:
    next_url = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return "/"
    return next_url


def send_comment_notification_async(comment):
    """Send notification in a background thread to avoid blocking the request."""

    if _is_test_environment():
        send_comment_notification(comment)
        return

    def _send():
        try:
            send_comment_notification(comment)
        finally:
            # 线程自建的数据库连接不会随 daemon 线程回收，必须显式关闭
            connections.close_all()

    threading.Thread(target=_send, daemon=True).start()


@require_POST
def create_comment(request):
    client_ip = get_client_ip(request)
    rate_key = f"comment-rate:{client_ip}"
    if cache.get(rate_key):
        messages.error(request, "提交过于频繁，请稍后再试。")
        return HttpResponseRedirect(_safe_next_url(request))

    # 无论成功与否都计入限流，避免绕过表单校验无限刷提交
    cache.set(
        rate_key,
        True,
        getattr(settings, "COMMENT_INTERVAL_SECONDS", 30),
    )

    form = CommentForm(request.POST)
    next_url = _safe_next_url(request)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = form.cleaned_data["post"]
        comment.ip_address = client_ip
        if request.user.is_authenticated:
            comment.user = request.user
            comment.is_approved = True
        comment.save()
        send_comment_notification_async(comment)
        messages.success(request, "评论已发布。" if comment.is_approved else "评论已提交，等待审核。")
    else:
        messages.error(request, "评论提交失败，请检查表单。")
    return HttpResponseRedirect(next_url)
