from django.contrib import admin
from django_mysql.models import QuerySet
from guardian.admin import GuardedModelAdmin

from seosnap.admin.extract_field import ExtractFieldInline
from seosnap.admin.page import PageAdmin
from seosnap.models import Website, website_add_permission_filter, Page


@admin.register(Website)
class WebsiteAdmin(GuardedModelAdmin):
    list_display = ('name', 'domain', 'sitemap', 'created_at', 'updated_at', 'cache_updated_at')
    readonly_fields = ('cache_updated_at',)
    list_display_links = ('name', 'domain')
    change_form_template = 'admin/seosnap/edit_website.html'

    inlines = [
        ExtractFieldInline
    ]

    def get_urls(self):
        from django.urls import path

        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super().get_urls()
        new_urls = [
            path('<path:object_id>/pages/', self.admin_site.admin_view(self.pages_view),
                 name='%s_%s_websitepages' % info),
            path('<path:website_id>/pages/<path:object_id>/change', self.admin_site.admin_view(self.page_view),
                 name='%s_%s_websitepages' % info),
        ]
        return new_urls + urls

    def get_queryset(self, request):
        qs: QuerySet = super().get_queryset(request)

        if request.user.is_superuser: return qs

        qs = website_add_permission_filter(qs, 'view_website', request.user)
        return qs

    def pages_view(self, request, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: PageAdmin = site._registry[Page]
        response = model.websitepages_view(request, object_id)

        filtered_query_set = response.context_data["cl"].queryset.filter(website=2)
        response.context_data["cl"].queryset = filtered_query_set
        return response

    def page_view(self, request, website_id=None, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: PageAdmin = site._registry[Page]
        response = model.websitepage_view(request, website_id, object_id, '')
        return response
