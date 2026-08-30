from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ..models import NavItem, Page


class PageTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            "staff", password="test-password", is_staff=True
        )
        self.page = Page.objects.create(
            title="关于",
            slug="about",
            content_markdown="## 关于我\n\n你好。",
            status="published",
        )

    def test_published_page_renders_at_top_level_url(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "关于我")
        self.assertContains(response, "<h2")

    def test_get_absolute_url(self):
        self.assertEqual(self.page.get_absolute_url(), "/about/")

    def test_draft_page_is_404_for_guest_and_visible_to_staff(self):
        self.page.status = "draft"
        self.page.save()
        self.assertEqual(self.client.get("/about/").status_code, 404)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/about/").status_code, 200)

    def test_reserved_slug_is_rejected(self):
        page = Page(title="搜索保留字", slug="search", content_markdown="x")
        with self.assertRaises(ValidationError):
            page.full_clean()

    def test_unknown_slug_falls_through_to_legacy_handler(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)

    def test_nav_item_can_link_to_page(self):
        NavItem.objects.create(title="关于", url=self.page.get_absolute_url(), order=1)
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, 'href="/about/"')
