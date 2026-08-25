from datetime import datetime, timezone as datetime_timezone
from pathlib import Path
import json
import re
import sqlite3

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from apps.comments.models import Comment

from .models import Category, Post


def normalize_emlog_legacy_url(post_id: int, alias: str = "") -> str:
    return f"/post-{post_id}.html" if not alias else f"/post/{alias}"


def unique_slug(base: str, existing_slugs: set[str]) -> str:
    slug = base or "emlog"
    candidate = slug
    counter = 2
    while candidate in existing_slugs:
        candidate = f"{slug}-{counter}"
        counter += 1
    existing_slugs.add(candidate)
    return candidate


def emlog_datetime(timestamp: int):
    if not timestamp:
        return None
    try:
        return datetime.fromtimestamp(int(timestamp), tz=datetime_timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def parse_emlog_tags(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,，]", raw)
    return [part.strip() for part in parts if part.strip()]


def load_sqlite_rows(database_path: str | Path, table: str) -> list[dict]:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
    finally:
        connection.close()


def read_emlog_export(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as export_file:
        payload = json.load(export_file)
    required = {"posts", "categories", "tags", "comments"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"Emlog 导出缺少字段：{', '.join(sorted(missing))}")
    return payload


@transaction.atomic
def import_emlog_data(data: dict, author_id=None) -> dict:
    User = get_user_model()
    author = User.objects.filter(pk=author_id).first() or User.objects.order_by("pk").first()
    if author is None:
        raise ValueError("目标站点至少需要一个用户作为导入作者")

    category_map = {}
    used_category_slugs = set(Category.objects.values_list("slug", flat=True))
    for row in sorted(data["categories"], key=lambda item: item.get("taxis") or 0):
        source_id = int(row.get("sid") or row["id"])
        name = (row.get("sortname") or row.get("name") or f"Emlog {source_id}").strip()
        base_slug = slugify(row.get("alias") or row.get("slug") or name) or f"emlog-{source_id}"
        slug = unique_slug(base_slug, used_category_slugs)
        if Category.objects.filter(name=name).exists():
            name = f"{name} ({source_id})"
        category = Category.objects.create(name=name, slug=slug)
        category_map[source_id] = category

    post_map = {}
    imported_tag_names = set()
    used_post_slugs = set(Post.objects.values_list("slug", flat=True))
    for row in data["posts"]:
        source_id = int(row.get("gid") or row["id"])
        title = (row.get("title") or f"Emlog {source_id}").strip()
        alias = row.get("alias") or ""
        base_slug = slugify(alias) or f"emlog-post-{source_id}"
        slug = unique_slug(base_slug, used_post_slugs)
        published = emlog_datetime(row.get("date") or row.get("published_at"))
        is_published = str(row.get("hide", row.get("status", "n"))).lower() in ("n", "published", "false")
        category = category_map.get(int(row.get("sortid") or 0))
        post, _ = Post.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "author": author,
                "category": category,
                "excerpt": row.get("excerpt") or "",
                "content_markdown": row.get("content") or "",
                "status": "published" if is_published and str(row.get("type", "blog")) == "blog" else "draft",
                "views": max(0, int(row.get("views") or 0)),
                "legacy_url": normalize_emlog_legacy_url(source_id),
                "published_at": published if is_published else None,
            },
        )
        post_map[source_id] = post

        row_tag_names = parse_emlog_tags(row.get("tags") or "")
        imported_tag_names.update(row_tag_names)
        post.tags.clear()
        if row_tag_names:
            post.tags.add(*row_tag_names)

    comment_source_ids = {}
    comments = data["comments"]
    ordered_comments = sorted(comments, key=lambda item: int(item.get("date") or 0))
    for _ in range(3):
        pending = [row for row in ordered_comments if int(row.get("cid") or row["id"]) not in comment_source_ids]
        progress = False
        for row in pending:
            source_id = int(row.get("cid") or row["id"])
            parent_id = int(row.get("pid") or 0)
            parent = comment_source_ids.get(parent_id)
            if parent_id and parent is None:
                continue
            post = post_map.get(int(row.get("gid") or row.get("post_id")))
            if post is None:
                continue
            created_at = emlog_datetime(row.get("date")) or datetime.now(tz=datetime_timezone.utc)
            guest_email = row.get("mail") or row.get("guest_email") or f"emlog-{source_id}@example.invalid"
            comment, _ = Comment.objects.update_or_create(
                post=post,
                guest_name=row.get("poster") or row.get("guest_name") or f"Emlog {source_id}",
                guest_email=guest_email,
                created_at=created_at,
                defaults={
                    "parent": parent,
                    "body": row.get("comment") or row.get("body") or "",
                    "is_approved": str(row.get("hide", "n")).lower() == "n",
                    "ip_address": row.get("ip") or None,
                },
            )
            comment_source_ids[source_id] = comment
            progress = True
        if not pending or not progress:
            break

    skipped_comments = len(ordered_comments) - len(comment_source_ids)
    return {
        "categories": len(category_map),
        "posts": len(post_map),
        "tags": len(imported_tag_names),
        "comments": len(comment_source_ids),
        "skipped_comments": max(0, skipped_comments),
        "author": author.username,
    }


def import_emlog_export(path: str | Path, author_id=None) -> dict:
    return import_emlog_data(read_emlog_export(path), author_id=author_id)


def import_emlog_sqlite(path: str | Path, author_id=None) -> dict:
    data = {
        "posts": load_sqlite_rows(path, "blog"),
        "categories": load_sqlite_rows(path, "sort"),
        "tags": load_sqlite_rows(path, "tag"),
        "comments": load_sqlite_rows(path, "comment"),
    }
    return import_emlog_data(data, author_id=author_id)
