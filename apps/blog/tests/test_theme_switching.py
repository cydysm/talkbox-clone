from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Post, ThemeSetting


class ThemeSwitchingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("author", password="test-password")
        self.post = Post.objects.create(
            title="主题切换",
            slug="theme-switch",
            author=self.user,
            content_markdown="# 正文",
            status="published",
        )

    def test_default_theme_is_used_without_database_setting(self):
        response = self.client.get(reverse("blog:post-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/themes/cactus_dark/css/main.css")

    def test_active_theme_is_loaded_dynamically(self):
        ThemeSetting.set_active("cactus_light")
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/themes/cactus_light/css/main.css")
        self.assertNotContains(response, "/static/themes/cactus_dark/css/main.css")

    def test_only_one_theme_remains_active(self):
        first = ThemeSetting.set_active("cactus_light")
        second = ThemeSetting.set_active("cactus_dark")
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)
        self.assertEqual(ThemeSetting.active_name(), "cactus_dark")

    def test_unknown_theme_is_rejected(self):
        with self.assertRaises(ValueError):
            ThemeSetting.set_active("unknown-theme")
