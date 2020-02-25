import coreapi, coreschema
from django.db import transaction

from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from seosnap.models import Website, QueueItem
from seosnap.serializers import QueueItemSerializer


class QueueWebsiteList(viewsets.ViewSet, PageNumberPagination):
    @decorators.action(detail=True, methods=['get'])
    def queue(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        data = website.queue_items.filter(status='unscheduled') \
                   .order_by('-priority', '-created_at') \
                   .all()[:50]

        with transaction.atomic():
            for item in data:
                item.status = 'scheduled'
                item.save()

        serializer = QueueItemSerializer(data, many=True)
        return Response(serializer.data)


class QueueWebsiteUpdate(viewsets.ViewSet):
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "items",
            location="body",
            schema=coreschema.Array(
                items=coreschema.Object(
                    properties={},
                    title="QueueItem",
                    description="QueueItem",
                )
            )
        ),
    ])

    @decorators.action(detail=True, methods=['put'])
    def update_queue(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        # TODO: this is a disastser
        items = request.data if isinstance(request.data, list) else []
        addresses = [item['page']['address'] for item in items if 'page' in item and 'address' in item['page']]

        existing = {item.page.address: item for item in
                    QueueItem.objects.filter(page__address__in=addresses, website_id=website_id)}
        allowed_fields = set(QueueItemSerializer.Meta.fields) - set(QueueItemSerializer.Meta.read_only_fields)

        for item in items:
            data = {k: item[k] for k in allowed_fields if k in item}
            if item['page']['address'] in existing:
                item = existing[item['page']['address']]
                for k, v in data.items(): setattr(item, k, v)

        with transaction.atomic():
            for item in existing.values():
                item.save()

        serializer = QueueItemSerializer(list(existing.values()), many=True)
        return Response(serializer.data)


class QueueWebsiteClean(viewsets.ViewSet):
    @decorators.action(detail=True, methods=['delete'])
    def clean_queue(self, request, version, website_id=None):
        website: Website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        website.queue_items.filter(status='completed').delete()

        return Response([])
