import coreapi, coreschema
from django.db import transaction
from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from seosnap.models import Page, Website
from seosnap.serializers import PageSerializer


class PageWebsiteList(viewsets.ViewSet, PageNumberPagination):
    @decorators.action(detail=True, methods=['get'])
    def pages(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        queryset = website.pages.all()

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = PageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PageSerializer(queryset, many=True)
        return Response(serializer.data)


class PageWebsiteUpdate(viewsets.ViewSet):
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "items",
            location="body",
            schema=coreschema.Array(
                items=coreschema.Object(
                    properties={},
                    title="Page",
                    description="Page",
                )
            )
        ),
    ])

    @decorators.action(detail=True, methods=['put'])
    def update_pages(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        items = request.data if isinstance(request.data, list) else []
        addresses = [item['address'] for item in items if 'address' in item]

        existing = {page.address: page for page in Page.objects.filter(address__in=addresses, website_id=website_id)}
        allowed_fields = set(PageSerializer.Meta.fields) - set(PageSerializer.Meta.read_only_fields)
        for item in items:
            item = {k: item[k] for k in allowed_fields if k in item}
            if item['address'] in existing:
                page = existing[item['address']]
                for k, v in item.items(): setattr(page, k, v)
            else:
                existing[item['address']] = Page(**item)

        with transaction.atomic():
            cache_updated_at = website.cache_updated_at
            for page in existing.values():
                page.website_id = website_id
                cache_updated_at = page.cached_at
                page.save()
            website.cache_updated_at = cache_updated_at
            website.save()

        serializer = PageSerializer(list(existing.values()), many=True)
        return Response(serializer.data)

class PageWebsiteClean(viewsets.ViewSet):
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "date",
            required=True,
            location="form",
            description="Delete all pages before this date/time YYYY-MM-DDTHH:MM:SS"
        ),
    ])

    @decorators.action(detail=True, methods=['delete'])
    def clean_pages(self, request, version, website_id=None):
        website: Website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        date = request.data['date'];

        if not date:
            return Response([])

        website.pages.filter(updated_at__lte=date).delete()

        return Response([])