from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.blog.models import Post

from .models import Comment
from .notifications import send_comment_notification


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CommentNotificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = get_user_model().objects.create_user(
            "author",
            email="author@example.com",
            password="test-password",
        )
        self.post = Post.objects.create(
            title="通知测试",
            slug="notification-test",
            author=self.author,
            content_markdown="正文",
            status="published",
            published_at=datetime(2026, 8, 25, tzinfo=datetime_timezone.utc),
        )

    def test_new_guest_comment_notifies_post_author(self):
        response = self.client.post(
            reverse("comments:create"),
            {
                "post": self.post.pk,
                "guest_name": "访客",
                "guest_email": "guest@example.com",
                "body": "新评论",
                "next": self.post.get_absolute_url(),
            },
        )
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["author@example.com"])
        self.assertIn("文章有新评论待审核：通知测试", mail.outbox[0].subject)
        self.assertIn("新评论", mail.outbox[0].body)

    def test_reply_notifies_parent_commenter(self):
        parent = Comment.objects.create(
            post=self.post,
            guest_name="原访客",
            guest_email="parent@example.com",
            body="原始评论",
            is_approved=True,
        )
        self.client.post(
            reverse("comments:create"),
            {
                "post": self.post.pk,
                "parent": parent.pk,
                "guest_name": "回复者",
                "guest_email": "reply@example.com",
                "body": "这是回复",
                "honeypot": "",
                "next": self.post.get_absolute_url(),
            },
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["parent@example.com"])
        self.assertIn("你的评论收到了新回复：通知测试", mail.outbox[0].subject)

    @override_settings(COMMENT_REPLY_NOTIFY=False)
    def test_reply_notifications_can_be_disabled(self):
        parent = Comment.objects.create(
            post=self.post,
            guest_name="原访客",
            guest_email="parent@example.com",
            body="原始评论",
            is_approved=True,
        )
        self.client.post(
            reverse("comments:create"),
            {
                "post": self.post.pk,
                "parent": parent.pk,
                "guest_name": "回复者",
                "guest_email": "reply@example.com",
                "body": "关闭回复提醒",
                "next": self.post.get_absolute_url(),
            },
        )
        self.assertEqual(len(mail.outbox), 0)

    @patch("apps.comments.notifications.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_notification_failure_does_not_break_submission(self, send_mail_mock):
        comment = Comment.objects.create(
            post=self.post,
            guest_name="访客",
            guest_email="guest@example.com",
            body="邮件失败也不影响评论",
            is_approved=True,
        )
        self.assertFalse(send_comment_notification(comment))
        send_mail_mock.assert_called_once()
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
