from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Category, Post


class BlogBrowsingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("author", password="test-password")
        cls.category = Category.objects.create(name="技术", slug="tech")
        cls.post = Post.objects.create(
            title="Django 搜索",
            slug="django-search",
            author=cls.user,
            category=cls.category,
            excerpt="搜索示例",
            content_markdown="# 正文\n\nDjango 内容",
            status="published",
        )
        cls.draft = Post.objects.create(
            title="草稿",
            slug="draft-post",
            author=cls.user,
            content_markdown="不应出现",
            status="draft",
        )
        cls.post.tags.add("Python")

    def test_category_page_shows_only_published_posts(self):
        response = self.client.get(reverse("blog:category-detail", args=["tech"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertNotContains(response, self.draft.title)

    def test_tag_page_shows_tagged_posts(self):
        tag_id = self.post.tags.first().pk
        response = self.client.get(reverse("blog:tag-detail", args=[tag_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertNotContains(response, self.draft.title)

    def test_search_matches_title_and_excludes_drafts(self):
        response = self.client.get(reverse("blog:search"), {"q": "Django"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertNotContains(response, self.draft.title)

    def test_empty_search_returns_all_published_posts(self):
        response = self.client.get(reverse("blog:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertNotContains(response, self.draft.title)
