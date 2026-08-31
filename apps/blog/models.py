import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from slugify import slugify
from taggit.managers import TaggableManager


def generate_unique_slug(instance, text, fallback_prefix):
    """从标题生成唯一 slug；中文由 python-slugify 转拼音，无可转写内容时用时间戳兜底。"""
    base = slugify(text)[:80].strip("-")
    if not base:
        base = f"{fallback_prefix}-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:4]}"
    slug = base
    existing = type(instance).objects.all()
    if instance.pk:
        existing = existing.exclude(pk=instance.pk)
    counter = 2
    while existing.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Category(models.Model):
    name = models.CharField("分类", max_length=80, unique=True)
    slug = models.SlugField("别名", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "分类"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.name

    @property
    def legacy_id(self) -> int | None:
        if self.slug.startswith("emlog-"):
            suffix = self.slug.removeprefix("emlog-")
            return int(suffix) if suffix.isdigit() else None
        return None


class ThemeSetting(models.Model):
    name = models.SlugField("主题标识", max_length=80, unique=True)
    is_active = models.BooleanField("当前启用", default=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "主题设置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.name}{'（启用）' if self.is_active else ''}"

    def clean(self):
        available = getattr(settings, "AVAILABLE_THEMES", None)
        if available and self.name not in available:
            raise ValidationError({"name": f"未知主题，可选：{', '.join(available)}"})

    def save(self, *args, **kwargs):
        if self.is_active:
            ThemeSetting.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def active_name(cls) -> str:
        default = getattr(settings, "THEME", "cactus_dark")
        active = cls.objects.filter(is_active=True).values_list("name", flat=True).first()
        return active or default

    @classmethod
    def set_active(cls, name: str):
        available = getattr(settings, "AVAILABLE_THEMES", [default_theme()])
        if name not in available:
            raise ValueError(f"未知主题：{name}")
        setting, _ = cls.objects.get_or_create(name=name, defaults={"is_active": False})
        setting.is_active = True
        setting.save(update_fields=["is_active", "updated_at"])
        return setting


class MarkdownSourceSetting(models.Model):
    is_enabled = models.BooleanField("显示原文按钮", default=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "Markdown 原文视图"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"Markdown 原文视图（{'启用' if self.is_enabled else '停用'}）"

    def save(self, *args, **kwargs):
        if not self.pk:
            existing = MarkdownSourceSetting.objects.first()
            if existing:
                existing.is_enabled = self.is_enabled
                existing.save()
                self.pk = existing.pk
                return
        super().save(*args, **kwargs)

    @classmethod
    def enabled(cls) -> bool:
        setting = cls.objects.first()
        return setting.is_enabled if setting else True


class SiteMeta(models.Model):
    name = models.CharField(
        "站点名称（显示）",
        max_length=100,
        blank=True,
        help_text="页面顶部大标题、页脚版权与 RSS 链接名称；留空时使用站点名称（SITE_NAME）。",
    )
    title = models.CharField(
        "网页标题",
        max_length=100,
        blank=True,
        help_text="浏览器标签页与 RSS 标题；留空时使用站点名称（SITE_NAME）。",
    )
    description = models.TextField(
        "站点描述（meta）",
        max_length=300,
        blank=True,
        help_text="meta description；留空时使用 SITE_DESCRIPTION。",
    )
    about = models.CharField(
        "主页简介",
        max_length=200,
        blank=True,
        help_text="显示在主页顶部，最长 200 字；留空时使用站点描述。",
    )
    favicon = models.ImageField(
        "Favicon",
        upload_to="site/",
        blank=True,
        null=True,
        help_text="建议 32×32 或 48×48 的 PNG/ICO；留空时不输出 favicon 链接。",
    )
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "站点设置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.name or self.title or "（使用默认标题）"

    def save(self, *args, **kwargs):
        if not self.pk:
            existing = SiteMeta.objects.first()
            if existing:
                self.pk = existing.pk
                existing.name = self.name
                existing.title = self.title
                existing.description = self.description
                existing.about = self.about
                if self.favicon:
                    existing.favicon = self.favicon
                existing.save()
                return
        super().save(*args, **kwargs)

    @classmethod
    def current_about(cls) -> str:
        setting = cls.objects.first()
        if setting and setting.about:
            return setting.about
        return settings.SITE_DESCRIPTION

    @classmethod
    def current_name(cls) -> str:
        setting = cls.objects.first()
        if setting and setting.name:
            return setting.name
        return settings.SITE_NAME

    @classmethod
    def current_title(cls) -> str:
        setting = cls.objects.first()
        if setting and setting.title:
            return setting.title
        return settings.SITE_NAME

    @classmethod
    def current_description(cls) -> str:
        setting = cls.objects.first()
        if setting and setting.description:
            return setting.description
        return settings.SITE_DESCRIPTION


class ShareTarget(models.Model):
    name = models.SlugField("目标", max_length=50, unique=True)
    order = models.PositiveSmallIntegerField("排序", default=0)
    is_visible = models.BooleanField("显示", default=True)

    class Meta:
        verbose_name = "分享目标"
        verbose_name_plural = verbose_name
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return self.label()

    def label(self) -> str:
        from .share_targets import SHARE_TARGETS

        return SHARE_TARGETS.get(self.name, {}).get("label", self.name)

    def clean(self):
        from .share_targets import SHARE_TARGETS

        if self.name not in SHARE_TARGETS:
            raise ValidationError(
                {"name": f"未知分享目标，可选：{', '.join(SHARE_TARGETS)}"}
            )


class PluginSetting(models.Model):
    name = models.SlugField("插件标识", max_length=100, unique=True)
    is_enabled = models.BooleanField("已启用", default=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "插件设置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.name}{'（启用）' if self.is_enabled else ''}"


def default_theme() -> str:
    return ThemeSetting.active_name()


class NavItem(models.Model):
    VISIBILITY_CHOICES = [
        ("all", "所有页面"),
        ("home", "仅主页"),
        ("non_home", "仅其它页面"),
        ("hidden", "隐藏"),
    ]

    title = models.CharField("标题", max_length=50)
    url = models.CharField("链接", max_length=200)
    order = models.PositiveSmallIntegerField("排序", default=0)
    visibility = models.CharField("显示范围", max_length=10, choices=VISIBILITY_CHOICES, default="all")
    show_in_post_header = models.BooleanField("显示在文章页顶部导航", default=True)

    class Meta:
        verbose_name = "导航链接"
        verbose_name_plural = verbose_name
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return f"{self.title}（{self.url}）"

    def clean(self):
        if self.visibility == "hidden":
            return
        existing = NavItem.objects.exclude(visibility="hidden")
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.count() >= settings.NAV_MAX_ITEMS:
            raise ValidationError(
                {"visibility": f"导航链接最多显示 {settings.NAV_MAX_ITEMS} 个。"}
            )


class Page(models.Model):
    RESERVED_SLUGS = {
        "post", "category", "tag", "search", "theme", "page", "archive",
        "admin", "control-panel", "static", "media", "comments",
        "media-api", "healthz",
    }
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("published", "已发布"),
    ]

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("路径", max_length=200, unique=True, blank=True)
    content_markdown = models.TextField("内容（Markdown）")
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "独立页面"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title, "page")
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("blog:page-detail", args=[self.slug])

    def clean(self):
        if self.slug in self.RESERVED_SLUGS:
            raise ValidationError({"slug": f"该路径为系统保留字：{', '.join(sorted(self.RESERVED_SLUGS))}"})


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("published", "已发布"),
    ]

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("别名", max_length=220, unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="作者",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="分类",
    )
    tags = TaggableManager(blank=True)
    excerpt = models.TextField("摘要", blank=True)
    content_markdown = models.TextField("Markdown 内容")
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="draft")
    views = models.PositiveIntegerField("浏览量", default=0)
    legacy_url = models.CharField(
        "Emlog 原链接",
        max_length=500,
        blank=True,
        db_index=True,
        help_text="例如 /post/123 或 /?post=123",
    )
    published_at = models.DateTimeField("发布时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["status", "-published_at"])]
        verbose_name = "文章"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title, "post")
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("blog:post-detail", args=[self.slug])

    @property
    def legacy_id(self) -> int | None:
        if self.legacy_url.startswith("/post-") or self.slug.startswith("emlog-post-"):
            suffix = self.slug.removeprefix("emlog-post-")
            if suffix.isdigit():
                return int(suffix)
        if self.legacy_url.startswith("/post-"):
            suffix = self.legacy_url[6:].removesuffix(".html")
            if suffix.isdigit():
                return int(suffix)
        return None

    def is_accessible_by(self, user) -> bool:
        return self.status == "published" or (
            user.is_authenticated and (user.is_staff or user == self.author)
        )
