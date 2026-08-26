import json
import re
import sqlite3
from datetime import datetime
from datetime import timezone as datetime_timezone
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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


def _iso_datetime(value) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime_timezone.utc)
        return int(parsed.timestamp())
    except (TypeError, ValueError):
        raise ValueError(f"无效时间格式：{value}") from None


def normalize_generic_export(data: dict) -> dict:
    if data.get("format") != "talkbox-generic":
        raise ValueError("通用导入必须使用 talkbox-generic 格式")
    if data.get("version") != 1:
        raise ValueError("通用导入仅支持协议版本 1")

    categories = []
    category_ids = set()
    for row in data.get("categories", []):
        source_id = int(row["id"])
        if source_id in category_ids:
            raise ValueError(f"分类 ID 重复：{source_id}")
        category_ids.add(source_id)
        name = str(row.get("name") or "").strip()
        if not name:
            raise ValueError(f"分类缺少名称：{source_id}")
        categories.append({
            "sid": source_id,
            "name": name,
            "slug": row.get("slug") or "",
        })

    posts = []
    post_ids = set()
    for row in data.get("posts", []):
        source_id = int(row["id"])
        if source_id in post_ids:
            raise ValueError(f"文章 ID 重复：{source_id}")
        post_ids.add(source_id)
        if not str(row.get("title") or "").strip():
            raise ValueError(f"文章缺少标题：{source_id}")
        if row.get("content_markdown") in (None, ""):
            raise ValueError(f"文章缺少 Markdown 内容：{source_id}")
        tags = row.get("tags", [])
        posts.append({
            "gid": source_id,
            "title": str(row.get("title") or "").strip(),
            "alias": row.get("slug") or "",
            "content": row.get("content_markdown") or "",
            "excerpt": row.get("excerpt") or "",
            "status": "published" if row.get("status") == "published" else "draft",
            "date": _iso_datetime(row.get("published_at")) or 0,
            "views": max(0, int(row.get("views") or 0)),
            "sortid": int(row["category_id"]) if row.get("category_id") is not None else 0,
            "tags": ",".join(str(tag).strip() for tag in tags if str(tag).strip()),
            "type": "blog",
            "hide": "n" if row.get("status") == "published" else "y",
            "generic_legacy_url": row.get("legacy_url") or "",
        })

    comments = []
    comment_ids = set()
    for row in data.get("comments", []):
        source_id = int(row["id"])
        if source_id in comment_ids:
            raise ValueError(f"评论 ID 重复：{source_id}")
        comment_ids.add(source_id)
        author_name = str(row.get("author_name") or "").strip()
        author_email = str(row.get("author_email") or "").strip()
        if not author_name:
            raise ValueError(f"评论缺少昵称：{source_id}")
        try:
            validate_email(author_email)
        except ValidationError:
            raise ValueError(f"评论邮箱无效：{source_id}") from None
        approved = row.get("is_approved", True) is True
        comments.append({
            "cid": source_id,
            "gid": int(row["post_id"]),
            "pid": int(row["parent_id"]) if row.get("parent_id") is not None else 0,
            "poster": author_name,
            "mail": author_email,
            "comment": row.get("body") or "",
            "date": _iso_datetime(row.get("created_at")) or 0,
            "hide": "n" if approved else "y",
        })

    missing_post_ids = {int(row["post_id"]) for row in data.get("comments", [])} - post_ids
    if missing_post_ids:
        raise ValueError(f"评论引用了不存在的文章：{', '.join(map(str, sorted(missing_post_ids)))}")
    unknown_category_ids = {
        int(row["category_id"]) for row in data.get("posts", [])
        if row.get("category_id") is not None
    } - category_ids
    if unknown_category_ids:
        raise ValueError(f"文章引用了不存在的分类：{', '.join(map(str, sorted(unknown_category_ids)))}")

    return {"categories": categories, "posts": posts, "tags": [], "comments": comments}


def read_generic_export(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as export_file:
        payload = json.load(export_file)
    required = {"format", "version", "posts"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"通用导出缺少字段：{', '.join(sorted(missing))}")
    return normalize_generic_export(payload)


@transaction.atomic
def import_generic_export(path: str | Path, author_id=None) -> dict:
    return import_emlog_data(read_generic_export(path), author_id=author_id)


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
                "legacy_url": row.get("generic_legacy_url") or normalize_emlog_legacy_url(source_id),
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
