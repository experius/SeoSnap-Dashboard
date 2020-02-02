import os

from django.contrib import admin
from django.utils.html import format_html

from seosnap.admin import WebsiteBaseAdmin
from seosnap.models import Page, Website


@admin.register(Page)
class PageAdmin(WebsiteBaseAdmin):
    list_display = (
        'address_link', 'address_full', 'content_type', 'status_code', 'cache_status', 'cached_at', 'created_at',
        'updated_at')

    readonly_fields = (
        'website', 'address', 'address_full', 'content_type', 'status_code', 'extract_fields', 'cache_status',
        'cached_at', 'created_at', 'updated_at')

    search_fields = ('address', 'content_type', 'status_code', 'extract_fields', 'cached_at')

    list_filter = ('status_code', 'content_type', 'cache_status')

    list_per_page = 50

    change_list_template = 'admin/seosnap/view_pages.html'
    change_form_template = 'admin/seosnap/edit_page.html'

    def address_link(self, page):
        url = f'/seosnap/website/{self.website.id}/pages/{page.id}/change'
        return format_html('<a href="{}">{}</a>', url, page.address)

    def address_full(self, page):
        return format_html('<a href="{}" target="_blank">Open page</a>', self.website.get_url(page))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def _edit(self, request, object_id=None, form_url='', extra_context=None):
        page = self.get_object(request, object_id)

        cacheserver_root = os.getenv('EXTERNAL_CACHE_SERVER_URL').rstrip('/')
        if len(cacheserver_root) == 0:
            cacheserver_root = f'http://{request.get_host().replace("8080", "5000")}/render'
        refresh_url = cacheserver_root + '/' + self.website.get_url(page)
        return super()._edit(request, object_id, form_url, {'refresh_url': refresh_url})
