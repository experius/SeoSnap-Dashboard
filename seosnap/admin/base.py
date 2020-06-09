from typing import Optional
from abc import ABC, abstractmethod

from django.contrib import admin

from seosnap.models import Website


class WebsiteBaseAdmin(admin.ModelAdmin):
    website: Optional[Website] = None

    def view_listing(self, request, website_id=None):
        self.website = Website.objects.get(id=website_id)
        return self._listing(request)

    def _listing(self, request, extra_content=None):
        _extra_content = {'title': f'{self.model.__name__} for Website: {self.website}', 'website': self.website}
        if extra_content: _extra_content = {**_extra_content, **extra_content}
        return self.changelist_view(request, _extra_content)

    def view_edit(self, request, website_id=None, object_id=None, form_url=''):
        self.website = Website.objects.get(id=website_id)
        return self._edit(request, object_id, form_url)

    def _edit(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context if extra_context else {}
        return self.changeform_view(request, object_id, form_url, {'website': self.website, **extra_context})

    def has_module_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.change_website', self.website) \
            or request.user.has_perm('seosnap.change_website')

    def has_view_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.view_website', self.website) \
            or request.user.has_perm('seosnap.view_website')

    def has_delete_permission(self, request, obj=None):
        if self.website is None: return False
        return request.user.has_perm('seosnap.change_website', self.website) \
            or request.user.has_perm('seosnap.change_website')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(website=self.website.id)
