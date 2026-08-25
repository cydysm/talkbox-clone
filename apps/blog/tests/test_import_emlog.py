from datetime import datetime, timezone as datetime_timezone
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Category, Post
from ..services import import_emlog_data


class EmlogImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("importer", password="test-password")
        fixture = Path(__file__).parent / "fixtures" / "emlog_export.json"
        import json

        with fixture.open(encoding="utf-8") as fixture_file:
            cls.result = import_emlog_data(json.load(fixture_file), author_id=cls.user.pk)

    def test_import_counts(self):
        self.assertEqual(self.result, {
            "categories": 1,
            "posts": 2,
            "tags": 2,
            "comments": 2,
            "skipped_comments": 0,
            "author": "importer",
        })

    def test_post_and_relationships_are_preserved(self):
        post = Post.objects.get(slug="emlog-first")
        self.assertEqual(post.status, "published")
        self.assertEqual(post.views, 37)
        self.assertEqual(post.legacy_url, "/post-1.html")
        self.assertEqual(post.legacy_id, 1)
        self.assertEqual(post.category.name, "技术")
        self.assertEqual(set(post.tags.values_list("name", flat=True)), {"Python", "迁移"})
        self.assertEqual(
            post.published_at,
            datetime.fromtimestamp(1756000000, tz=datetime_timezone.utc),
        )

    def test_comment_tree_is_rebuilt(self):
        post = Post.objects.get(slug="emlog-first")
        root = post.comments.get(guest_email="visitor@example.com")
        reply = post.comments.get(guest_email="owner@example.com")
        self.assertIsNone(root.parent)
        self.assertEqual(reply.parent, root)

    def test_legacy_urls_redirect_permanently(self):
        post = Post.objects.get(slug="emlog-first")
        for url in ("/post-1.html", "/post/1", "/?post=1"):
            response = self.client.get(url)
            with self.subTest(url=url):
                self.assertRedirects(response, post.get_absolute_url(), status_code=301)

    def test_category_name_collision_is_resolved(self):
        category = Category.objects.create(name="新分类", slug="existing")
        data = {
            "posts": [],
            "categories": [{"sid": 9, "sortname": "新分类", "alias": "new"}],
            "tags": [],
            "comments": [],
        }
        result = import_emlog_data(data, author_id=self.user.pk)
        imported = Category.objects.get(slug="new")
        self.assertEqual(result["categories"], 1)
        self.assertNotEqual(imported.pk, category.pk)
        self.assertEqual(imported.name, "新分类 (9)")
