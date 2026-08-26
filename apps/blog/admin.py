from django.contrib import admin

from .models import Category, PluginSetting, Post, ThemeSetting


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

    @admin.action(description="发布所选文章")
    def publish_posts(self, request, queryset):
        updated = 0
        from django.utils import timezone

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
        self.message_user(request, f"已将 {updated} 篇文章转为草稿。")


@admin.register(ThemeSetting)
class ThemeSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "updated_at"]
    list_editable = ["is_active"]


@admin.register(PluginSetting)
class PluginSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_enabled", "updated_at"]
    list_editable = ["is_enabled"]
