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

    def test_post_detail_renders_markdown_and_provides_source_view(self):
        url = reverse("blog:post-detail", args=[self.post.slug])
        rendered = self.client.get(url)

        self.assertContains(rendered, "<h1>正文</h1>")
        self.assertContains(rendered, "Markdown 原文")
        self.assertNotContains(rendered, 'class="post-source"')

        source = self.client.get(url, {"view": "markdown"})

        self.assertContains(source, 'class="post-source"')
        self.assertContains(source, "# 正文")
        self.assertContains(source, "返回正文")
        self.assertNotContains(source, "<h1>正文</h1>")

        fallback = self.client.get(url, {"view": "invalid"})
        self.assertContains(fallback, "<h1>正文</h1>")

    def test_empty_search_returns_all_published_posts(self):
        response = self.client.get(reverse("blog:search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertNotContains(response, self.draft.title)

    def test_post_lists_are_paginated(self):
        for number in range(2, 14):
            Post.objects.create(
                title=f"分页文章 {number}",
                slug=f"paged-post-{number}",
                author=self.user,
                content_markdown="内容",
                status="published",
            )
        with self.settings(POSTS_PER_PAGE=5):
            first_page = self.client.get(reverse("blog:post-list"))
            second_page = self.client.get(reverse("blog:post-list"), {"page": "2"})
            invalid_page = self.client.get(reverse("blog:post-list"), {"page": "999"})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(invalid_page.status_code, 200)
        self.assertContains(first_page, '<span class="current">1</span>')
        self.assertContains(first_page, '<a href="?page=2">2</a>')
        self.assertContains(second_page, '<span class="current">2</span>')
        self.assertContains(second_page, '<a href="?page=1">1</a>')
        self.assertContains(invalid_page, '<span class="current">1</span>')
