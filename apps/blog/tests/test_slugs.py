from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import Page, Post


class SlugGenerationTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user("writer", password="test-password")

    def _post(self, title, **kwargs):
        return Post(title=title, author=self.author, content_markdown="正文", status="published", **kwargs)

    def test_chinese_title_gets_pinyin_slug(self):
        post = self._post("数据库索引选择的思考框架")
        post.save()
        self.assertEqual(post.slug, "shu-ju-ku-suo-yin-xuan-ze-de-si-kao-kuang-jia")
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

    def test_mixed_title_keeps_latin_part(self):
        post = self._post("Hello World 测试")
        post.save()
        self.assertEqual(post.slug, "hello-world-ce-shi")

    def test_duplicate_titles_get_unique_slugs(self):
        first = self._post("重复标题")
        first.save()
        second = self._post("重复标题")
        second.save()
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.startswith(first.slug + "-"))

    def test_untransliterable_title_falls_back_to_prefix(self):
        post = self._post("🚀🚀🚀")
        post.save()
        self.assertTrue(post.slug.startswith("post-"))
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

    def test_manual_slug_is_preserved(self):
        post = self._post("手工别名", slug="my-own-slug")
        post.save()
        self.assertEqual(post.slug, "my-own-slug")

    def test_page_slug_generated_from_chinese_title(self):
        page = Page.objects.create(title="关于我们", content_markdown="正文", status="published")
        self.assertEqual(page.slug, "guan-yu-wo-men")
        self.assertEqual(self.client.get(page.get_absolute_url()).status_code, 200)

    def test_slug_validation_still_rejects_conflicts(self):
        self._post("已有文章", slug="taken").save()
        post = self._post("另一篇", slug="taken")
        with self.assertRaises(ValidationError):
            post.full_clean()
