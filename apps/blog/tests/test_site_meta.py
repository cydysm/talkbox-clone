from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from ..models import Post, SiteMeta


class SiteMetaAboutTests(TestCase):
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
        SiteMeta.objects.create(about="这里记录我的技术笔记与生活随笔。")
        response = self.client.get(reverse("blog:post-list"))
        self.assertContains(response, "这里记录我的技术笔记与生活随笔。")
        # 默认站点描述不应再出现在主页简介区（meta description 的回退不算）
        self.assertNotContains(response, '<section id="about"><p>Talkbox Clone - Python blog</p>')

    def test_text_is_capped(self):
        setting = SiteMeta(about="超" * 201)
        with self.assertRaises(ValidationError):
            setting.full_clean()

    def test_single_row_is_reused(self):
        pre = SiteMeta.objects.first()
        print("DEBUG pre:", None if pre is None else (pre.pk, pre.about, pre.name, pre.title))
        first = SiteMeta.objects.create(about="第一版")
        print("DEBUG first.pk:", first.pk, "count:", SiteMeta.objects.count(),
              "db pk:", SiteMeta.objects.first().pk)
        second = SiteMeta.objects.create(about="第二版")
        print("DEBUG second.pk:", second.pk, "count:", SiteMeta.objects.count())
        self.assertEqual(SiteMeta.objects.count(), 1)
        self.assertEqual(SiteMeta.objects.first().about, "第二版")
        self.assertEqual(second.pk, SiteMeta.objects.first().pk)


class AdminDashboardTests(TestCase):
    def test_dashboard_renders_for_staff(self):
        staff = get_user_model().objects.create_user(
            "dash-viewer", password="test-password", is_staff=True, is_superuser=True
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "内容管理")
        self.assertContains(response, "站点配置")
        self.assertContains(response, "互动管理")
