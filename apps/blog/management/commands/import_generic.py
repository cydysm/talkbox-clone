from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.blog.services import import_generic_export


class Command(BaseCommand):
    help = "导入 talkbox-generic v1 JSON 导出，支持文章、分类、标签和树形评论。"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=Path)
        parser.add_argument("--author-id", type=int, default=None)

    def handle(self, *args, **options):
        input_file = options["input_file"]
        if not input_file.exists():
            raise CommandError(f"输入文件不存在：{input_file}")
        if input_file.suffix.lower() != ".json":
            raise CommandError("通用导入目前仅支持 .json 文件")
        try:
            result = import_generic_export(input_file, author_id=options["author_id"])
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(
            f"作者 {result['author']}；导入分类 {result['categories']} 个、"
            f"文章 {result['posts']} 篇、标签引用 {result['tags']} 个、"
            f"评论 {result['comments']} 条；跳过评论 {result['skipped_comments']} 条。"
        ))
