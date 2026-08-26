from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

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


@override_settings(PLUGIN_DIRS=[])
class PluginDependencyTests(TestCase):
    def _discover(self, plugin_dir):
        with override_settings(PLUGIN_DIRS=[plugin_dir]):
            registry.discover()

    def test_missing_requirements_block_plugin_discovery(self):
        plugin_dir = self._write_plugin(
            manifest={"name": "Broken Plugin", "version": "1.0.0"},
            requirements=["definitely-missing-talkbox-package==1.2.3"],
        )
        with self.assertRaises(RuntimeError) as context:
            self._discover(plugin_dir)
        self.assertIn("插件依赖未安装：definitely-missing-talkbox-package==1.2.3", str(context.exception))

    def test_installed_dependency_allows_discovery(self):
        plugin_dir = self._write_plugin(
            manifest={"name": "Django Dependency Plugin", "version": "1.0.0"},
            requirements=["Django>=4"],
            module="def transform_html(value):\n    return value\n",
        )
        self._discover(plugin_dir)
        self.assertIn("Django Dependency Plugin", [item.name for item in registry.available()])

    @staticmethod
    def _write_plugin(manifest, requirements=None, module=None):
        import json
        import tempfile

        root = Path(tempfile.mkdtemp(prefix="talkbox-plugins-"))
        plugin_dir = root / "sample"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        if requirements is not None:
            (plugin_dir / "requirements.txt").write_text("\n".join(requirements), encoding="utf-8")
        if module is not None:
            (plugin_dir / "__init__.py").write_text("", encoding="utf-8")
            (plugin_dir / "plugin.py").write_text(module, encoding="utf-8")
        return root
