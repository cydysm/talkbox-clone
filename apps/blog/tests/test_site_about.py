from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ..models import Post, SiteAbout


class SiteAboutTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user("writer", password="test-password")
        self.post = Post.objects.create(
            title="主页简介",
            slug="about-text",
            author=self.author,
            content_markdown="正文",
            status="published",
        )

    def test_falls_back_to_site_description(self):
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, "Talkbox Clone - Python blog")

    def test_admin_text_is_rendered_on_homepage(self):
        SiteAbout.objects.create(text="这里记录我的技术笔记与生活随笔。")
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, "这里记录我的技术笔记与生活随笔。")
        self.assertNotContains(response, "Talkbox Clone - Python blog")

    def test_text_is_capped(self):
        setting = SiteAbout(text="超" * 201)
        with self.assertRaises(ValidationError):
            setting.full_clean()

    def test_single_row_is_reused(self):
        SiteAbout.objects.create(text="第一版")
        second = SiteAbout.objects.create(text="第二版")
        self.assertEqual(SiteAbout.objects.count(), 1)
        self.assertEqual(SiteAbout.objects.first().text, "第二版")
        self.assertEqual(second.pk, SiteAbout.objects.first().pk)
