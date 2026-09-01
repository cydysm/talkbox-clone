from datetime import datetime
from datetime import timezone as datetime_timezone

from django.test import TestCase
from django.urls import reverse

from apps.blog.models import Post


class CommentMessagingTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.user = None
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user("author", password="test-password")
        self.post = Post.objects.create(
            title="评论提示",
            slug="comment-messaging",
            author=user,
            content_markdown="正文",
            status="published",
            published_at=datetime(2026, 8, 26, tzinfo=datetime_timezone.utc),
        )
        self.url = reverse("comments:create")

    def test_guest_sees_pending_message(self):
        response = self.client.post(self.url, {
            "post": self.post.pk,
            "guest_name": "访客",
            "guest_email": "guest@example.com",
            "body": "测试评论",
            "honeypot": "",
            "next": self.post.get_absolute_url(),
        }, follow=True)
        messages_list = list(response.context["messages"])
        self.assertTrue(any("等待审核" in str(m) for m in messages_list), f"Messages: {[str(m) for m in messages_list]}")

    def test_staff_sees_published_message(self):
        from django.contrib.auth import get_user_model

        admin = get_user_model().objects.create_superuser("staff-admin", "admin@example.com", "pass1234")
        self.client.force_login(admin)
        response = self.client.post(self.url, {
            "post": self.post.pk,
            "guest_name": "站长",
            "guest_email": "staff@example.com",
            "body": "站长回复",
            "honeypot": "",
            "next": self.post.get_absolute_url(),
        }, follow=True)
        messages_list = list(response.context["messages"])
        self.assertTrue(any("已发布" in str(m) for m in messages_list), f"Messages: {[str(m) for m in messages_list]}")
