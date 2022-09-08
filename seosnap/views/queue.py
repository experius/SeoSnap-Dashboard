import coreapi, coreschema
from django.db import transaction
from datetime import datetime, timedelta, timezone

from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from django.http.response import HttpResponse

from seosnap.models import Website, QueueItem
from seosnap.serializers import QueueItemSerializer, QueueSerializer


class QueueWebsiteList(viewsets.ViewSet, PageNumberPagination):

    @decorators.action(detail=True, methods=['post'])
    def redo_old(self, request, version, website_id=None):
        doCacheAgain = datetime.now(timezone.utc) - timedelta(minutes=120)

        QueueItem.objects \
            .filter(status='scheduled') \
            .filter(website_id=website_id) \
            .filter(updated_at__lte=doCacheAgain.date())\
            .update(status='unscheduled')

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['get'])
    def queue(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        data = website.queue_items.filter(status='unscheduled') \
                   .order_by('priority', '-created_at') \
                   .all()[:25]

        with transaction.atomic():
            for item in data:
                item.status = 'scheduled'
                item.save()

        serializer = QueueItemSerializer(data, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['get'])
    def queue_progress(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()

        if request.GET.get('filter'):
            queryset = website.queue_items.filter(status__in=['scheduled', 'unscheduled']).filter(page__address__icontains=request.GET.get('filter'))
        else:
            queryset = website.queue_items.filter(status__in=['scheduled', 'unscheduled'])

        if request.GET.get('limit'):
            self.page_size = request.GET.get('limit')

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = QueueSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = QueueSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['get'])
    def todo_count(self, request, version, website_id=None):
        queItemCount = QueueItem.objects\
            .filter(website_id=website_id)\
            .filter(status__in=['scheduled', 'unscheduled'])\
            .count()

        return Response(queItemCount)


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
    def update_priority(self, request, version, queue_item_id=None):
        print("im hereee")
        item = QueueItem.objects \
            .filter(id=queue_item_id) \
            .first()

        if item is None:
            return HttpResponse(status=404)

        item.priority = 1
        item.save()

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['post'])
    def items_update_priority(self, request, version):
        QueueItem.objects \
            .filter(id__in=request.data.values()) \
            .update(priority=10)

        return HttpResponse(status=200)

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

    @decorators.action(detail=True, methods=['delete'])
    def delete_queue_item(self, request, version, queue_item_id=None):
        QueueItem.objects \
            .filter(id=queue_item_id) \
            .delete()

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['post'])
    def delete_multiple_queue_items(self, request, version):
        QueueItem.objects.filter(id__in=request.data.values()).delete()

        return HttpResponse(status=200)


class Queues(viewsets.ViewSet, PageNumberPagination):

    @decorators.action(detail=True, methods=['get'])
    def get_queues(self, request, version):
        website_ids = []
        if request.query_params.getlist('website_ids'):
            website_ids = request.query_params.getlist('website_ids')

        if request.GET.get('filter'):
            queryset = QueueItem.objects.filter(website_id__in=website_ids).filter(status__in=['scheduled', 'unscheduled']).filter(page__address__icontains=request.GET.get('filter')).all()
        else:
            queryset = QueueItem.objects.filter(website_id__in=website_ids).filter(status__in=['scheduled', 'unscheduled']).all()

        if request.GET.get('limit'):
            self.page_size = request.GET.get('limit')

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = QueueSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = QueueSerializer(queryset, many=True)
        return Response(serializer.data)
