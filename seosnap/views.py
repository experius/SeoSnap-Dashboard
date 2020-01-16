import coreapi
import coreschema
from rest_framework import versioning, viewsets, generics, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema, get_schema_view, DefaultSchema
from rest_framework.views import APIView

from seosnap.models import Website, Page
from seosnap.serializers import WebsiteSerializer, PageSerializer
from rest_framework.schemas import AutoSchema, ManualSchema

custom_schema = ManualSchema(
    fields=[
        coreapi.Field(
            "id",
            required=True,
            location="path",
            schema=coreschema.String(
                title="ID",
                description="Foobar ID.",
            )
        ),
        coreapi.Field(
            "foobar",
            location="query",
            schema=coreschema.String(
                title="Foobar",
                description="Foobar?",
            )
        ),
    ],
    description="Foobar!",
)


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer


class PageWebsiteList(viewsets.ViewSet, PageNumberPagination):
    @action(detail=True, methods=['get'])
    def pages(self, request, version, website_id=None):
        queryset = Website.objects.get(id=website_id).pages.all()

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
                    properties={
                        'aa': coreschema.Boolean()
                    },
                    title="Page",
                    description="Page",
                )
            )
        ),
    ])

    @action(detail=True, methods=['put'], schema=custom_schema)
    def update_pages(self, request, version, website_id=None):
        items = request.data if isinstance(request.data, list) else []
        addresses = [item['address'] for item in items if 'address' in item]

        existing = {item.address: item for item in Page.objects.filter(address__in=addresses)}
        allowed_fields = set(PageSerializer.Meta.fields) - set(PageSerializer.Meta.read_only_fields)
        for item in items:
            item = {k: item[k] for k in allowed_fields if k in item}
            test = Page(item)
            aa = 0

        model = Website.objects.get(id=website_id).pages

        queryset = self.get_object().pages.all()
        serializer = PageSerializer(queryset, many=True)
        return Response(serializer.data)
