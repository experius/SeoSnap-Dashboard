from django.contrib import admin
from .models import Website, Page


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    pass


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    readonly_fields = ['address', 'content_type', 'status_code', 'extract_fields', 'cache_status', 'cached_at',
                       'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
