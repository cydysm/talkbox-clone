import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Comment


logger = logging.getLogger(__name__)


def build_comment_notification(comment: Comment) -> tuple[str, str, list[str]]:
    post_url = comment.post.get_absolute_url()
    if comment.parent:
        subject = f"你的评论收到了新回复：{comment.post.title}"
        recipient = comment.parent.guest_email
        if comment.parent.user and comment.parent.user.email:
            recipient = comment.parent.user.email
        template = "comments/emails/reply_notification.txt"
    else:
        subject = f"文章有新评论待审核：{comment.post.title}"
        owner_email = getattr(settings, "NOTIFY_EMAIL", "")
        if not owner_email and comment.post.author.email:
            owner_email = comment.post.author.email
        recipient = owner_email
        template = "comments/emails/new_comment_notification.txt"
    body = render_to_string(
        template,
        {
            "comment": comment,
            "post_url": post_url,
            "site_name": settings.SITE_NAME,
        },
    )
    return subject, body, [recipient] if recipient else []


def send_comment_notification(comment: Comment):
    if comment.parent and not getattr(settings, "COMMENT_REPLY_NOTIFY", True):
        return False
    try:
        subject, body, recipients = build_comment_notification(comment)
        if not recipients:
            return False
        sent_count = send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        return bool(sent_count)
    except Exception:
        logger.exception("发送评论通知失败 comment_id=%s", comment.pk)
        return False
