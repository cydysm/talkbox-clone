from django.contrib import admin, messages
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import Truncator

from apps.comments.models import Comment

from .models import (
    Category,
    MarkdownSourceSetting,
    NavItem,
    Page,
    PluginSetting,
    Post,
    ShareTarget,
    SiteAbout,
    ThemeSetting,
)

admin.site.site_header = "Talkbox 管理后台"
admin.site.site_title = "Talkbox"
admin.site.index_title = "站点概览"


_original_index = admin.site.index


def dashboard_index(request, extra_context=None):
    week_ago = timezone.now() - timezone.timedelta(days=7)
    stats = {
        "total_posts": Post.objects.count(),
        "published_posts": Post.objects.filter(status="published").count(),
        "draft_posts": Post.objects.filter(status="draft").count(),
        "total_views": Post.objects.aggregate(total=Sum("views"))["total"] or 0,
        "total_comments": Comment.objects.count(),
        "pending_comments": Comment.objects.filter(is_approved=False).count(),
        "recent_comments": (
            Comment.objects.filter(is_approved=False)
            .select_related("post")
            .order_by("-created_at")[:5]
        ),
        "posts_this_week": Post.objects.filter(created_at__gte=week_ago).count(),
    }
    return _original_index(request, extra_context={**(extra_context or {}), **stats})


admin.site.index = dashboard_index
admin.site.index_template = "admin/dashboard.html"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
    list_display = ["title", "url", "order", "visibility"]
    list_editable = ["order", "visibility"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "content_markdown"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["created_at", "updated_at"]
    view_on_site = True

    class Media:
        css = {"all": ("admin/markdown_editor.css",)}
        js = ("admin/markdown_editor.js",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "views", "published_at"]
    list_filter = ["status", "category", "tags"]
    search_fields = ["title", "content_markdown", "legacy_url"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["views", "created_at", "updated_at"]
    date_hierarchy = "published_at"
    actions = ["publish_posts", "unpublish_posts"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "excerpt"]}),
        ("内容", {"fields": ["content_markdown"]}),
        ("发布", {"fields": ["status", "published_at", "author", "category", "tags"]}),
        ("元数据", {"fields": ["views", "created_at", "updated_at", "legacy_url"], "classes": ["collapse"]}),
    ]

    class Media:
        css = {"all": ("admin/markdown_editor.css",)}
        js = ("admin/markdown_editor.js",)

    def get_changeform_initial_data(self, request):
        return {"author": request.user}

    @admin.action(description="发布所选文章")
    def publish_posts(self, request, queryset):
        updated = 0
        for post in queryset:
            if post.status != "published":
                post.status = "published"
                if post.published_at is None:
                    post.published_at = timezone.now()
                post.save(update_fields=["status", "published_at", "updated_at"])
                updated += 1
        self.message_user(request, f"已发布 {updated} 篇文章。")

    @admin.action(description="转为草稿")
    def unpublish_posts(self, request, queryset):
        updated = queryset.exclude(status="draft").update(status="draft")
        self.message_user(request, f"已将 {updated} 篇转为草稿。")


@admin.register(ThemeSetting)
class ThemeSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "updated_at"]
    actions = ["set_active_theme"]

    @admin.action(description="设为当前主题")
    def set_active_theme(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "请只勾选一个主题进行启用。", level=messages.ERROR)
            return
        setting = ThemeSetting.set_active(queryset.first().name)
        self.message_user(request, f"已启用主题「{setting.name}」。")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # is_active 通过「设为当前主题」action 切换，不提供逐字段编辑
        return False


@admin.register(PluginSetting)
class PluginSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_enabled", "updated_at"]
    list_editable = ["is_enabled"]


@admin.register(MarkdownSourceSetting)
class MarkdownSourceSettingAdmin(admin.ModelAdmin):
    list_display = ["__str__", "is_enabled", "updated_at"]
    list_editable = ["is_enabled"]

    def has_add_permission(self, request):
        return not MarkdownSourceSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShareTarget)
class ShareTargetAdmin(admin.ModelAdmin):
    list_display = ["label", "name", "order", "is_visible"]
    list_editable = ["order", "is_visible"]


@admin.register(SiteAbout)
class SiteAboutAdmin(admin.ModelAdmin):
    list_display = ["text", "updated_at"]

    def has_add_permission(self, request):
        return not SiteAbout.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
