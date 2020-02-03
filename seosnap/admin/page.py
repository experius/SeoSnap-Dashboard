import os

from django.contrib import admin
from django.db import transaction
from django.shortcuts import redirect
from django.utils.html import format_html
from rest_framework.reverse import reverse

from seosnap.admin import WebsiteBaseAdmin
from seosnap.models import Page, QueueItem


def enqueue(admin_model, request, queryset):
    page_ids = queryset.values_list('id', flat=True)

    with transaction.atomic():
        for page_id in page_ids:
            item = QueueItem(page_id=page_id, website_id=admin_model.website.id, priority=10000)
            item.save()

    return redirect(reverse('admin:seosnap_website_websitequeue', args=(admin_model.website.id,)))


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

    ordering = ('-cached_at',)

    change_list_template = 'admin/seosnap/view_pages.html'
    change_form_template = 'admin/seosnap/edit_page.html'

    actions = [enqueue]

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
