import json
from datetime import datetime
from datetime import timezone as datetime_timezone
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Category, Post
from ..services import import_emlog_data, import_generic_export, normalize_generic_export


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


class GenericImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("generic-importer", password="test-password")
        cls.payload = {
            "format": "talkbox-generic",
            "version": 1,
            "categories": [{"id": 7, "name": "通用分类", "slug": "generic"}],
            "posts": [{
                "id": 42,
                "title": "旧博客文章",
                "slug": "legacy-post",
                "content_markdown": "# Hello",
                "excerpt": "摘要",
                "status": "published",
                "published_at": "2026-01-02T03:04:05Z",
                "views": 18,
                "category_id": 7,
                "tags": ["Generic", "迁移"],
                "legacy_url": "/old-blog/42/",
            }],
            "comments": [
                {
                    "id": 101,
                    "post_id": 42,
                    "parent_id": None,
                    "author_name": "访客",
                    "author_email": "guest@example.com",
                    "body": "根评论",
                    "created_at": "2026-01-03T08:00:00Z",
                    "is_approved": True,
                },
                {
                    "id": 102,
                    "post_id": 42,
                    "parent_id": 101,
                    "author_name": "站长",
                    "author_email": "owner@example.com",
                    "body": "子回复",
                    "created_at": "2026-01-03T09:00:00Z",
                    "is_approved": False,
                },
            ],
        }

    def test_import_preserves_content_and_relationships(self):
        result = import_generic_export(self._write_payload(self.payload), author_id=self.user.pk)
        post = Post.objects.get(slug="legacy-post")
        root = post.comments.get(guest_email="guest@example.com")
        reply = post.comments.get(guest_email="owner@example.com")

        self.assertEqual(result["categories"], 1)
        self.assertEqual(result["posts"], 1)
        self.assertEqual(result["tags"], 2)
        self.assertEqual(result["comments"], 2)
        self.assertEqual(result["skipped_comments"], 0)
        self.assertEqual(post.status, "published")
        self.assertEqual(post.views, 18)
        self.assertEqual(post.legacy_url, "/old-blog/42/")
        self.assertEqual(set(post.tags.values_list("name", flat=True)), {"Generic", "迁移"})
        self.assertIsNone(root.parent)
        self.assertEqual(reply.parent, root)
        self.assertFalse(reply.is_approved)

    def test_legacy_url_redirects_permanently(self):
        import_generic_export(self._write_payload(self.payload), author_id=self.user.pk)
        post = Post.objects.get(slug="legacy-post")
        self.assertRedirects(self.client.get("/old-blog/42/"), post.get_absolute_url(), status_code=301)

    def test_invalid_protocol_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_generic_export({**self.payload, "format": "unknown"})
        with self.assertRaises(ValueError):
            normalize_generic_export({**self.payload, "version": 2})

    def test_broken_references_rollback_import(self):
        payload = {
            **self.payload,
            "comments": [{**self.payload["comments"][0], "id": 201, "post_id": 999}],
        }
        before_count = Post.objects.count()
        with self.assertRaises(ValueError):
            import_generic_export(self._write_payload(payload), author_id=self.user.pk)
        self.assertEqual(Post.objects.count(), before_count)

    @staticmethod
    def _write_payload(payload):
        import tempfile

        descriptor, filename = tempfile.mkstemp(suffix=".json")
        output = Path(filename)
        output.write_text(json.dumps(payload), encoding="utf-8")
        return output
