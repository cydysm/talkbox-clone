import threading

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

from .notifications import send_comment_notification

from .forms import CommentForm


def _is_test_environment():
    import sys

    return "test" in sys.argv


def send_comment_notification_async(comment):
    """Send notification in a background thread to avoid blocking the request."""

    if _is_test_environment():
        send_comment_notification(comment)
        return
    thread = threading.Thread(target=send_comment_notification, args=(comment,), daemon=True)
    thread.start()


@require_POST
def create_comment(request):
    client_ip = request.META.get("REMOTE_ADDR") or "unknown"
    rate_key = f"comment-rate:{client_ip}"
    if cache.get(rate_key):
        messages.error(request, "提交过于频繁，请稍后再试。")
        return HttpResponseRedirect(request.POST.get("next", "/"))

    form = CommentForm(request.POST)
    next_url = request.POST.get("next", "/")
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = form.cleaned_data["post"]
        comment.ip_address = client_ip
        if request.user.is_authenticated:
            comment.user = request.user
            comment.is_approved = True
        comment.save()
        cache.set(
            rate_key,
            True,
            getattr(settings, "COMMENT_INTERVAL_SECONDS", 30),
        )
        send_comment_notification_async(comment)
        messages.success(request, "评论已发布。" if comment.is_approved else "评论已提交，等待审核。")
    else:
        messages.error(request, "评论提交失败，请检查表单。")
    return HttpResponseRedirect(next_url)
