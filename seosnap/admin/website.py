from typing import Optional

from django.contrib import admin
from django.utils.html import format_html
from django_mysql.models import QuerySet
from guardian.admin import GuardedModelAdmin

from seosnap.admin import QueueAdmin
from seosnap.admin.extract_field import ExtractFieldInline
from seosnap.admin.page import PageAdmin
from seosnap.helpers import permissons
from seosnap.models import Website, Page, QueueItem


@admin.register(Website)
class WebsiteAdmin(GuardedModelAdmin):
    list_display = ('name_link', 'domain', 'sitemap', 'created_at', 'updated_at', 'cache_updated_at')
    readonly_fields = ('cache_updated_at',)
    list_display_links = ('domain',)
    change_form_template = 'admin/seosnap/edit_website.html'

    inlines = [
        ExtractFieldInline
    ]

    def get_urls(self):
        from django.urls import path

        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super().get_urls()
        new_urls = [
            path('<path:object_id>/pages/', self.admin_site.admin_view(self.page_listing),
                 name='%s_%s_websitepages' % info),
            path('<path:website_id>/pages/<path:object_id>/change', self.admin_site.admin_view(self.page_edit),
                 name='%s_%s_websitepages_change' % info),
            # Do something about duplicates
            path('<path:object_id>/queue/', self.admin_site.admin_view(self.queue_listing),
                 name='%s_%s_websitequeue' % info),
            path('<path:website_id>/queue/add', self.admin_site.admin_view(self.queue_add),
                 name='%s_%s_websitequeue_add' % info),
            path('<path:website_id>/queue/<path:object_id>/change', self.admin_site.admin_view(self.queue_edit),
                 name='%s_%s_websitequeue_change' % info),
        ]
        return new_urls + urls

    def name_link(self, website):
        url = f'/seosnap/website/{website.id}/pages'
        return format_html('<a href="{}">{}</a>', url, website.name)

    def get_queryset(self, request):
        qs: QuerySet = super().get_queryset(request)
        return permissons.filter_permitted_websites(qs, request.user)

    def page_listing(self, request, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: PageAdmin = site._registry[Page]
        return model.view_listing(request, object_id)

    def page_edit(self, request, website_id=None, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: PageAdmin = site._registry[Page]
        return model.view_edit(request, website_id, object_id)

    def queue_listing(self, request, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: QueueAdmin = site._registry[QueueItem]
        return model.view_listing(request, object_id)

    def queue_edit(self, request, website_id=None, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: QueueAdmin = site._registry[QueueItem]
        return model.view_edit(request, website_id, object_id)

    def queue_add(self, request, website_id=None):
        site: admin.AdminSite = self.admin_site
        model: QueueAdmin = site._registry[QueueItem]
        return model.view_edit(request, website_id, None)
