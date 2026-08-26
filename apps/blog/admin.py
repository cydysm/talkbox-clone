from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone

from apps.comments.models import Comment

from .models import Category, PluginSetting, Post, ThemeSetting

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


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "views", "published_at"]
    list_filter = ["status", "category", "tags"]
    search_fields = ["title", "content_markdown", "legacy_url"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["views", "created_at", "updated_at"]
    date_hierarchy = "published_at"
    actions = ["publish_posts", "unpublish_posts"]

    class Media:
        css = {"all": ("admin/markdown_editor.css",)}
        js = ("admin/markdown_editor.js",)

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
    list_editable = ["is_active"]


@admin.register(PluginSetting)
class PluginSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_enabled", "updated_at"]
    list_editable = ["is_enabled"]
