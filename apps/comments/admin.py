from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["guest_name", "post", "parent", "is_approved", "created_at", "ip_address"]
    list_filter = ["is_approved", "post", "created_at"]
    search_fields = ["guest_name", "guest_email", "body", "post__title"]
    readonly_fields = ["ip_address", "created_at"]
    autocomplete_fields = ["post", "parent", "user"]
    actions = ["approve_comments", "reject_comments"]

    @admin.action(description="批准所选评论")
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"已批准 {updated} 条评论。")

    @admin.action(description="撤回所选评论")
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"已撤回 {updated} 条评论。")
