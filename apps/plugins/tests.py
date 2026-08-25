from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import PluginSetting, Post

from .registry import registry


class PluginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("author", password="test-password")
        self.post = Post.objects.create(
            title="插件测试",
            slug="plugin-test",
            author=self.user,
            content_markdown="[FOOTNOTE]",
            status="published",
        )
        registry.discover()

    def test_example_plugin_is_discovered(self):
        names = [plugin.name for plugin in registry.available()]
        self.assertIn("Markdown Footnote", names)

    def test_disabled_plugin_does_not_change_content(self):
        cache.clear()
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "[FOOTNOTE]")
        self.assertNotContains(response, "plugin-footnote")

    def test_enabled_plugin_transforms_html(self):
        PluginSetting.objects.create(name="Markdown Footnote", is_enabled=True)
        registry.discover()

        cache.clear()
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "plugin-footnote")
        self.assertNotContains(response, "[FOOTNOTE]")

    def test_enabled_state_persists(self):
        setting = PluginSetting.objects.create(name="Markdown Footnote", is_enabled=True)
        setting.refresh_from_db()
        self.assertTrue(setting.is_enabled)
