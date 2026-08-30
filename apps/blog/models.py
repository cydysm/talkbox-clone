from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


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
    title = models.CharField("标题", max_length=50)
    url = models.CharField("链接", max_length=200)
    order = models.PositiveSmallIntegerField("排序", default=0)
    is_visible = models.BooleanField("显示", default=True)

    class Meta:
        verbose_name = "导航链接"
        verbose_name_plural = verbose_name
        ordering = ["order", "pk"]

    def __str__(self) -> str:
        return f"{self.title}（{self.url}）"

    def clean(self):
        if not self.is_visible:
            return
        existing = NavItem.objects.filter(is_visible=True)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.count() >= settings.NAV_MAX_ITEMS:
            raise ValidationError(
                {"is_visible": f"导航链接最多显示 {settings.NAV_MAX_ITEMS} 个。"}
            )


class Page(models.Model):
    RESERVED_SLUGS = {
        "post", "category", "tag", "search", "theme", "page",
        "admin", "control-panel", "static", "media", "comments",
        "media-api", "healthz",
    }
    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("published", "已发布"),
    ]

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("路径", max_length=200, unique=True)
    content_markdown = models.TextField("内容（Markdown）")
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "独立页面"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.title

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
    slug = models.SlugField("别名", max_length=220, unique=True)
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

    def __str__(self) -> str:
        return self.title

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
