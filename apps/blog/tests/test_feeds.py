from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Post


class FeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("author", password="test-password")
        cls.post = Post.objects.create(
            title="Feed Post",
            slug="feed-post",
            author=cls.user,
            excerpt="Feed summary",
            content_markdown="# Body",
            status="published",
        )
        Post.objects.create(
            title="Hidden Draft",
            slug="hidden-draft",
            author=cls.user,
            content_markdown="secret",
            status="draft",
        )

    def test_rss_contains_published_post_only(self):
        response = self.client.get(reverse("rss"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        content = response.content.decode()
        self.assertIn("<title>Feed Post</title>", content)
        self.assertNotIn("Hidden Draft", content)

    def test_atom_contains_published_post_only(self):
        response = self.client.get(reverse("atom"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/atom+xml; charset=utf-8")
        content = response.content.decode()
        self.assertIn("<title>Feed Post</title>", content)
        self.assertNotIn("Hidden Draft", content)

    def test_feed_limit_is_respected(self):
        for number in range(25):
            Post.objects.create(
                title=f"Post {number}",
                slug=f"feed-post-{number}",
                author=self.user,
                content_markdown="Body",
                status="published",
            )
        with self.settings(FEED_LIMIT=10):
            response = self.client.get(reverse("rss"))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.content.decode().count("<item>"), 10)
