from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Post, SiteMeta


class MarkdownSourceTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user("writer", password="test-password")
        self.post = Post.objects.create(
            title="原文视图",
            slug="source-view",
            author=self.author,
            content_markdown="# 正文",
            status="published",
        )
        self.url = self.post.get_absolute_url()

    def test_enabled_by_default(self):
        self.assertTrue(SiteMeta.current_show_markdown_source())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Markdown 原文")

    def test_markdown_view_works_when_enabled(self):
        response = self.client.get(self.url + "?view=markdown")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "post-source")

    def test_disabled_hides_button_and_redirects_markdown_view(self):
        SiteMeta.objects.create(show_markdown_source=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Markdown 原文")
        redirect = self.client.get(self.url + "?view=markdown")
        self.assertRedirects(redirect, self.url, status_code=302, target_status_code=200)

    def test_site_settings_changelist_accessible(self):
        staff = get_user_model().objects.create_user("admin-x", password="test-password", is_staff=True, is_superuser=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:blog_sitemeta_changelist"))
        self.assertEqual(response.status_code, 200)
