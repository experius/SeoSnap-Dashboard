import os

from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.utils.html import format_html
from django_mysql.models import QuerySet
from guardian.admin import GuardedModelAdmin

from .models import Website, Page, ExtractField, website_add_permission_filter


class ExtractFieldInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance.id is None:
            kwargs['initial'] = [{
                'name': 'title',
                'css_selector': 'title',
                'display': True,
            }]
        super().__init__(*args, **kwargs)


class ExtractFieldInline(admin.TabularInline):
    model = ExtractField
    formset = ExtractFieldInlineFormset


@admin.register(ExtractField)
class ExtractFieldAdmin(admin.ModelAdmin):
    list_display = ('website', 'name', 'css_selector', 'display', 'created_at', 'updated_at')

    def has_module_permission(self, request):
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = (
        'address_link', 'address_full', 'content_type', 'status_code', 'cache_status', 'cached_at', 'created_at',
        'updated_at')

    readonly_fields = (
        'website', 'address', 'address_full', 'content_type', 'status_code', 'extract_fields', 'cache_status',
        'cached_at', 'created_at', 'updated_at')

    search_fields = ('address', 'content_type', 'status_code', 'extract_fields', 'cached_at')

    website = None
    change_list_template = 'admin/seosnap/view_pages.html'
    change_form_template = 'admin/seosnap/edit_page.html'

    list_filter = ('status_code', 'content_type', 'cache_status')

    def address_link(self, page):
        url = f'/seosnap/website/{self.website.id}/pages/{page.id}/change'
        return format_html('<a href="{}">{}</a>', url, page.address)

    def address_full(self, page):
        return format_html('<a href="{}" target="_blank">Open page</a>', self.website.get_url(page))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return False

    def websitepages_view(self, request, website_id=None):
        self.website = Website.objects.get(id=website_id)
        extra_context = {'title': f'Pages for Website: {self.website}', 'website': self.website}
        response = self.changelist_view(request, extra_context)
        return response

    def websitepage_view(self, request, website_id=None, page_id=None, form_url=''):
        self.website = Website.objects.get(id=website_id)
        page = self.get_object(request, page_id)

        cacheserver_root = os.getenv('EXTERNAL_CACHE_SERVER_URL').rstrip('/')
        if len(cacheserver_root) == 0:
            cacheserver_root = f'http://{request.get_host().replace("8080", "5000")}/render'
        refresh_url = cacheserver_root + '/' + self.website.get_url(page)
        response = self.changeform_view(request, page_id, form_url, {"refresh_url": refresh_url})
        return response

    def has_change_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.change_website', self.website)

    def has_view_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.view_website', self.website)

    def has_delete_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.change_website', self.website)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(website=self.website.id)


@admin.register(Website)
class WebsiteAdmin(GuardedModelAdmin):
    list_display = ('name', 'domain', 'sitemap', 'created_at', 'updated_at', 'cache_updated_at')
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
