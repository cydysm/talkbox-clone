from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.blog.models import Category, Post
from apps.blog.seed_data import DEMO_ARTICLES


class Command(BaseCommand):
    help = "创建或更新 15 篇本地演示文章。"

    def add_arguments(self, parser):
        parser.add_argument("--author-id", type=int, default=None)

    def handle(self, *args, **options):
        author = self.get_author(options["author_id"])
        category_names = sorted({article["category"] for article in DEMO_ARTICLES})
        categories = {
            name: Category.objects.get_or_create(
                slug=self.category_slug(name),
                defaults={"name": name},
            )[0]
            for name in category_names
        }

        created_count = 0
        updated_count = 0
        base_time = timezone.now()
        for index, article in enumerate(DEMO_ARTICLES, start=1):
            published_at = base_time - timezone.timedelta(days=len(DEMO_ARTICLES) - index)
            post, created = Post.objects.update_or_create(
                slug=article["slug"],
                defaults={
                    "title": article["title"],
                    "author": author,
                    "category": categories[article["category"]],
                    "excerpt": article["excerpt"],
                    "content_markdown": article["content"],
                    "status": "published",
                    "published_at": published_at,
                },
            )
            post.tags.set(article["tags"])
            created_count += int(created)
            updated_count += int(not created)

        self.stdout.write(self.style.SUCCESS(
            f"作者 {author.username}；新增 {created_count} 篇、更新 {updated_count} 篇。"
        ))

    def get_author(self, author_id):
        user_model = get_user_model()
        if author_id is not None:
            author = user_model.objects.filter(pk=author_id).first()
            if author is None:
                raise CommandError(f"作者 ID {author_id} 不存在")
            return author

        return (
            user_model.objects.filter(is_superuser=True).first()
            or user_model.objects.filter(is_staff=True).first()
            or user_model.objects.create_user(
                username="demo",
                email="demo@example.com",
                password="demo-password-2026",
            )
        )

    @staticmethod
    def category_slug(name):
        mapping = {
            "开发笔记": "dev-notes",
            "产品设计": "product-design",
            "效率工具": "productivity",
            "生活记录": "life-notes",
            "技术随笔": "tech-essays",
        }
        return mapping[name]
