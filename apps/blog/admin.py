from django.contrib import admin

from .models import Category, Post, ThemeSetting


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


@admin.register(ThemeSetting)
class ThemeSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "updated_at"]
    list_editable = ["is_active"]
