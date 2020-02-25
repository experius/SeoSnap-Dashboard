from django.contrib import admin
from django.forms import BaseInlineFormSet

from seosnap.models import ExtractField


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

