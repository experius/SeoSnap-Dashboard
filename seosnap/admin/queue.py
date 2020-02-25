from django.contrib import admin
from django.shortcuts import redirect
from rest_framework.reverse import reverse

from seosnap.admin import WebsiteBaseAdmin, format_html
from seosnap.models import QueueItem, Page


@admin.register(QueueItem)
class QueueAdmin(WebsiteBaseAdmin):
    list_display = ('queue_link', 'priority', 'status', 'created_at', 'updated_at')
    readonly_fields = ('website', 'status', 'created_at', 'updated_at')

    list_per_page = 50

    ordering = ('-updated_at',)

    change_list_template = 'admin/seosnap/view_queue.html'
    change_form_template = 'admin/seosnap/edit_queue.html'

    def save_model(self, request, obj, form, change):
        obj.website_id = self.website.id
        super().save_model(request, obj, form, change)

    def queue_link(self, queue_item: QueueItem):
        url = f'/seosnap/website/{self.website.id}/queue/{queue_item.id}/change'
        return format_html('<a href="{}">{}</a>', url, queue_item.page.address)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "page":
            kwargs["queryset"] = Page.objects.filter(website_id=self.website.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj: return ['page', *self.readonly_fields]
        else: return self.readonly_fields

    def response_add(self, request, obj, post_url_continue=None):
        res = super().response_add(request, obj, post_url_continue)
        return redirect(reverse('admin:seosnap_website_websitequeue_change', args=(self.website.id, obj.pk,)))

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        if '_save' in request.POST:
            return redirect(reverse('admin:seosnap_website_websitequeue', args=(self.website.id,)))
        else:
            return redirect(reverse('admin:seosnap_website_websitequeue_change', args=(self.website.id, obj.pk,)))
