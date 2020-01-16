from django.contrib import admin

from .models import Website, Page, ExtractField


class ExtractFieldInline(admin.TabularInline):
    model = ExtractField


@admin.register(ExtractField)
class ExtractFieldAdmin(admin.ModelAdmin):
    list_display = ('website', 'name', 'css_selector', 'created_at', 'updated_at')

    def has_module_permission(self, request):
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('address', 'content_type', 'status_code', 'cache_status', 'cached_at', 'created_at',
                    'updated_at')

    readonly_fields = ('content_type', 'status_code', 'extract_fields', 'cache_status',
                       'cached_at', 'created_at', 'updated_at')

    search_fields = ('address', 'content_type', 'status_code', 'extract_fields', 'cached_at')

    website_id = None
    change_list_template = 'admin/seosnap/view_pages.html'
    change_form_template = 'admin/seosnap/edit_page.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return False

    def websitepages_view(self, request, website_id=None):
        self.website_id = website_id
        website = Website.objects.get(id=website_id)
        extra_context = {'title': f'Pages for Website: {website}', 'website': website}
        response = self.changelist_view(request, extra_context)
        return response

    def get_queryset(self, request):
        return super().get_queryset(request).filter(website=self.website_id)


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'created_at', 'updated_at')
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
            path('<path:object_id>/pages/', self.admin_site.admin_view(self.pages_view), name='%s_%s_websitepages' % info),
        ]
        return new_urls + urls

    def pages_view(self, request, object_id=None):
        site: admin.AdminSite = self.admin_site
        model: PageAdmin = site._registry[Page]
        response = model.websitepages_view(request, object_id)

        filtered_query_set = response.context_data["cl"].queryset.filter(website=2)
        response.context_data["cl"].queryset = filtered_query_set

        return response
