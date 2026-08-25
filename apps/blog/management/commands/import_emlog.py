from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.blog.services import import_emlog_export, import_emlog_sqlite


class Command(BaseCommand):
    help = "导入 Emlog 文章、分类、标签和评论。支持 JSON 导出或 SQLite 数据库。"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=Path)
        parser.add_argument("--author-id", type=int, default=None)

    def handle(self, *args, **options):
        input_file = options["input_file"]
        if not input_file.exists():
            raise CommandError(f"输入文件不存在：{input_file}")
        try:
            if input_file.suffix.lower() == ".json":
                result = import_emlog_export(input_file, author_id=options["author_id"])
            elif input_file.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
                result = import_emlog_sqlite(input_file, author_id=options["author_id"])
            else:
                raise CommandError("仅支持 .json 或 .sqlite/.sqlite3/.db 文件")
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(self.format_result(result)))

    def format_result(self, result):
        return (
            f"作者 {result['author']}；导入分类 {result['categories']} 个、"
            f"文章 {result['posts']} 篇、标签引用 {result['tags']} 个、评论 {result['comments']} 条；"
            f"跳过评论 {result['skipped_comments']} 条。"
        )
