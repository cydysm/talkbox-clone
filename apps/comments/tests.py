from datetime import datetime, timedelta, timezone as datetime_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import Post

from .models import Comment


class CommentDisplayTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("author", password="test-password")
        self.post = Post.objects.create(
            title="评论时间",
            slug="comment-time",
            author=user,
            content_markdown="正文",
            status="published",
            published_at=datetime(2026, 8, 25, tzinfo=datetime_timezone.utc),
        )

    def test_comment_page_shows_created_at_for_nested_comments(self):
        parent = Comment.objects.create(
            post=self.post,
            guest_name="访客",
            guest_email="guest@example.com",
            body="父评论",
            is_approved=True,
        )
        Comment.objects.filter(pk=parent.pk).update(
            created_at=datetime(2026, 8, 25, 1, 30, tzinfo=datetime_timezone(timedelta(hours=8))),
        )
        Comment.objects.create(
            post=self.post,
            parent=parent,
            guest_name="站长",
            guest_email="owner@example.com",
            body="子回复",
            is_approved=True,
        )
        Comment.objects.filter(guest_email="owner@example.com").update(
            created_at=datetime(2026, 8, 25, 2, 45, tzinfo=datetime_timezone(timedelta(hours=8))),
        )
        response = self.client.get(reverse("blog:post-detail", args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<time datetime="2026-08-25T01:30:00+08:00">2026-08-25 01:30</time>')
        self.assertContains(response, '<time datetime="2026-08-25T02:45:00+08:00">2026-08-25 02:45</time>')
