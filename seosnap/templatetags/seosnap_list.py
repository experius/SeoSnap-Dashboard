from itertools import chain

from django.contrib.admin.templatetags.admin_list import result_headers, result_hidden_fields, ResultList, \
    items_for_result
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django import template
from django.utils.html import format_html

from seosnap.models import Website, Page

register = template.Library()


def custom_field_headers(website):
    for field in website.get_display_extract_fields():
        yield {
            "text": field.title(),
            "sortable": False,
            "sorted": False,
            "ascending": "asc",
            "class_attrib": format_html(' class="column-{}"', field),
        }


def custom_items_for_result(cl, result, website: Website):
    for field in website.get_display_extract_fields():
        value = result.get_extract_field(field)
        yield format_html('<td class="field-{}">{}</td>', field, value if value else '-')


def results(cl, website):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield ResultList(form, chain(items_for_result(cl, res, form), custom_items_for_result(cl, res, website)))
    else:
        for res in cl.result_list:
            yield ResultList(None, chain(items_for_result(cl, res, None), custom_items_for_result(cl, res, website)))


def result_list(cl, website):
    """
    Display the headers and data list together.
    """
    headers = list(result_headers(cl)) + list(custom_field_headers(website))
    num_sorted_fields = 0

    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {
        'cl': cl,
        'result_hidden_fields': list(result_hidden_fields(cl)),
        'result_headers': headers,
        'num_sorted_fields': num_sorted_fields,
        'results': list(results(cl, website)),
    }


@register.tag(name='result_list_custom')
def result_list_tag(parser, token):
    return InclusionAdminNode(
        parser, token,
        func=result_list,
        template_name='seosnap/change_list_results_pages.html',
        takes_context=False,
    )


def extractfield_list(model: Page, website: Website):
    fields = []
    for field in website.get_extract_fields():
        fields.append((field.title(), model.get_extract_field(field) if model.get_extract_field(field) else '-'))

    return {
        'fields': fields,
    }


@register.tag(name='extractfield_list')
def extractfield_list_tag(parser, token):
    return InclusionAdminNode(
        parser, token,
        func=extractfield_list,
        template_name='seosnap/extractfield_list.html',
        takes_context=False,
    )
