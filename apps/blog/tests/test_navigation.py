from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ..models import NavItem
from ..theme_preferences import get_nav_items


class NavigationTests(TestCase):
    def test_empty_nav_falls_back_to_home(self):
        items = get_nav_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "首页")
        self.assertEqual(items[0].url, "/")

    def test_visible_nav_items_render_in_order(self):
        NavItem.objects.create(title="归档", url="/archives/", order=2)
        NavItem.objects.create(title="关于", url="/about/", order=1)
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, ">关于</a>")
        self.assertContains(response, ">归档</a>")
        self.assertLess(response.content.decode().index(">关于</a>"), response.content.decode().index(">归档</a>"))

    def test_hidden_nav_items_are_not_rendered(self):
        NavItem.objects.create(title="关于", url="/about/", is_visible=False)
        response = self.client.get(reverse("blog:post-list"))
        self.assertNotContains(response, ">关于</a>")

    def test_nav_items_are_capped(self):
        for index in range(settings.NAV_MAX_ITEMS):
            NavItem.objects.create(title=f"菜单{index}", url=f"/menu-{index}/")
        extra = NavItem(title="超出", url="/extra/")
        with self.assertRaises(ValidationError):
            extra.full_clean()

    def test_cap_ignores_hidden_items(self):
        for index in range(settings.NAV_MAX_ITEMS):
            NavItem.objects.create(title=f"菜单{index}", url=f"/menu-{index}/")
        hidden = NavItem.objects.create(title="隐藏项", url="/hidden/", is_visible=False)
        hidden.title = "隐藏项改名"
        hidden.full_clean()

    def test_updating_existing_item_does_not_count_itself(self):
        item = NavItem.objects.create(title="关于", url="/about/")
        for index in range(settings.NAV_MAX_ITEMS - 1):
            NavItem.objects.create(title=f"菜单{index}", url=f"/menu-{index}/")
        item.url = "/about-me/"
        item.full_clean()
