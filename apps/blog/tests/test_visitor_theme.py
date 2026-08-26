from django.test import TestCase
from django.urls import reverse


class VisitorThemeTests(TestCase):
    def test_default_preference_follows_site_theme(self):
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, "/static/themes/cactus_dark/css/main.css")
        self.assertContains(response, 'value="system" aria-current="true"')

    def test_explicit_preference_is_stored_and_restored(self):
        response = self.client.post(
            reverse("blog:theme-switch"),
            {"theme": "light", "next": "/search/?q=hello"},
        )
        self.assertRedirects(response, "/search/?q=hello")
        self.assertEqual(response.cookies["visitor_theme"].value, "light")

        self.client.cookies["visitor_theme"] = response.cookies["visitor_theme"].value

        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, "/static/themes/cactus_light/css/main.css")
        self.assertContains(response, "/static/themes/cactus_dark/css/main.css", count=0)

    def test_system_preference_uses_media_queries(self):
        self.client.cookies["visitor_theme"] = "system"
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, 'media="(prefers-color-scheme: dark)"')
        self.assertContains(response, 'media="(prefers-color-scheme: light)"')

    def test_invalid_preference_is_rejected(self):
        response = self.client.post(
            reverse("blog:theme-switch"),
            {"theme": "neon"},
        )
        self.assertEqual(response.status_code, 400)

    def test_unsafe_next_url_is_ignored(self):
        response = self.client.post(
            reverse("blog:theme-switch"),
            {"theme": "light", "next": "https://example.com/"},
        )
        self.assertRedirects(response, "/")
