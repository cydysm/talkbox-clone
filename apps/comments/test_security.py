from datetime import datetime
from datetime import timezone as datetime_timezone

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.blog.models import Post

from .models import Comment


@override_settings(COMMENT_INTERVAL_SECONDS=60)
class CommentSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user("author", password="test-password")
        self.post = Post.objects.create(
            title="评论安全",
            slug="comment-security",
            author=self.user,
            content_markdown="正文",
            status="published",
            published_at=datetime(2026, 8, 26, tzinfo=datetime_timezone.utc),
        )
        self.url = reverse("comments:create")
        self.payload = {
            "post": self.post.pk,
            "guest_name": "访客",
            "guest_email": "guest@example.com",
            "body": "正常评论",
            "honeypot": "",
            "next": self.post.get_absolute_url(),
        }

    def test_honeypot_submission_is_rejected(self):
        payload = {**self.payload, "honeypot": "spam"}
        response = self.client.post(self.url, payload)
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(Comment.objects.count(), 0)

    def test_same_ip_cannot_submit_before_interval_expires(self):
        first = self.client.post(
            self.url,
            {**self.payload, "guest_email": "first@example.com"},
            REMOTE_ADDR="203.0.113.10",
        )
        second = self.client.post(
            self.url,
            {**self.payload, "guest_email": "second@example.com"},
            REMOTE_ADDR="203.0.113.10",
        )
        self.assertRedirects(first, self.post.get_absolute_url())
        self.assertRedirects(second, self.post.get_absolute_url())
        self.assertEqual(Comment.objects.count(), 1)

    def test_different_ips_are_independent(self):
        self.client.post(self.url, self.payload, REMOTE_ADDR="203.0.113.10")
        self.client.post(
            self.url,
            {**self.payload, "guest_email": "other@example.com"},
            REMOTE_ADDR="203.0.113.20",
        )
        self.assertEqual(Comment.objects.count(), 2)
