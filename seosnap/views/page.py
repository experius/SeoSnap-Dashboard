import coreapi, coreschema, requests, xmltodict
import xml.etree.ElementTree as ET
from django.db import transaction
from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from datetime import datetime, timedelta, timezone
from django.db.models import Q

from seosnap.models import Page, Website, QueueItem
from seosnap.models.sitemap import Sitemap
from seosnap.serializers import PageSerializer
from django.core import serializers
from django.http.response import JsonResponse, HttpResponse
from django.core.serializers import serialize
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict


class PageWebsiteList(viewsets.ViewSet, PageNumberPagination):
    @decorators.action(detail=True, methods=['get'])
    def pages(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        if request.GET.get('filter'):
            queryset = list(
                filter(lambda page: page.address.startswith(request.GET.get('filter')), website.pages.all()))
        else:
            queryset = website.pages.all()

        if request.GET.get('limit'):
            self.page_size = request.GET.get('limit')

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = PageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PageSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['get'])
    def count(self, request, version, website_id=None):
        pagesCount = Page.objects \
            .filter(website_id=website_id) \
            .count()

        return Response(pagesCount)

    def _multiThreadedPageSync(self, website_id, website, urlsData, doCacheAgain):
        print("start: _multiThreadedPageSync")
        createQueueObjects = []
        urlsList = set()
        count = 0

        for urlData in urlsData:
            urlsList.add(urlData['loc'])

        existingPages = list(
            Page.objects.filter(website_id=website_id).filter(address__in=urlsList).values_list('address',
                                                                                                'updated_at'))
        addresses = Page.objects.values_list('address', flat=True)

        print(addresses)

        for urlData in urlsData:

            if urlData['loc'] in addresses:
                if urlData['loc'] in urlsList:
                    urlsList.remove(urlData['loc'])

                # print(type(existingPages))
                for page in existingPages:

                    if page[0] == urlData['loc'] and urlData['lastmod'] is not None:
                        # if last mod is longer than X min ago
                        # Or later than page updated at
                        # [1] => updated_at

                        sitemapDiff = page[1] - urlData['lastmod']
                        rendertronDiff = page[1] - doCacheAgain
                        if (sitemapDiff.total_seconds() <= 0) or (rendertronDiff.total_seconds() <= 0):
                            print("do queue again")

                            queue_item_found = QueueItem.objects.filter(page=page).filter(status="unscheduled").first()
                            if queue_item_found is None:
                                queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                                createQueueObjects.append(queue_item)

        createPageObjects = []

        print("HOII <------")
        print(len(urlsData))
        print(len(urlsList))
        print(count)
        for url in urlsList:
            print("create: " + str(url))

            page: Page = Page(address=url, website=website)
            createPageObjects.append(page)

        Page.objects.bulk_create(createPageObjects)
        pages = Page.objects.filter(address__in=urlsList, website_id=website_id)

        for page in pages:
            queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
            createQueueObjects.append(queue_item)

        QueueItem.objects.bulk_create(createQueueObjects)

    @decorators.action(detail=True, methods=['get'])
    def sync(self, request, version, website_id=None):
        print("start call")
        website = Website.objects.filter(id=website_id).first()

        sitemap = Sitemap(website)
        urlsData = sitemap.get_data()

        doCacheAgain = datetime.now(timezone.utc) - timedelta(minutes=10000)

        print("-- overview --")
        print("total url count: " + str(len(urlsData)))
        print("-- start sync --")

        size = 500
        for i in range(0, len(urlsData), size):
            data = urlsData[i:i + size]
            self._multiThreadedPageSync(website_id, website, data, doCacheAgain)

        print("-- start delete --")

        urlList = map(lambda x: x["loc"], urlsData)
        deletablePages = Page.objects.filter(website_id=website_id).exclude(address__in=urlList) \
            .exclude(id__in=QueueItem.objects.filter(status="unscheduled").values('page_id'))

        urlsList = set()
        for urlData in urlsData:
            urlsList.add(urlData['loc'])

        for page in deletablePages:
            head, sep, tail = page.address.partition('?')

            if head.strip() not in urlsList:
                print("delete: " + str(head))
                QueueItem.objects.filter(page=page).delete()
                page.delete()

        print("-- fully delete --")

        return HttpResponse(status=200)


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


class RedoPageCache(viewsets.ViewSet):

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_tag(self, request, version, website_id=None):
        website: Website = Website.objects.filter(id=website_id).first()
        tags = request.data['tags']
        print(tags)
        print(tags.split(' '))

        query = Q()
        for tag in tags.split(' '):
            query |= Q(x_magento_tags__contains=tag)

        queryset = website.pages.all().filter(query)

        print(len(queryset))

        # urlList = []
        createQueueObjects = []
        # for p in queryset:
        #     urlList.append(p.address)
        #
        # print(len(urlList))
        itemsFound = QueueItem.objects.filter(page__in=queryset).filter(status="unscheduled").values_list('page_id', flat=True)
        print(itemsFound)

        for p in queryset:
            if p.id not in itemsFound:
                queue_item: QueueItem = QueueItem(page=p, website=website, priority=request.data['priority'])
                createQueueObjects.append(queue_item)

        QueueItem.objects.bulk_create(createQueueObjects)

        # Length of queryset

        # All pages
        print('xx')
        print(request)

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_website(self, request, version, website_id=None):
        print(" --- start request ---")

        website: Website = Website.objects.filter(id=website_id).first()
        if request.data['pageId']:
            prio = 10000
            if request.data['priority']:
                prio = 1

            page: Page = website.pages.filter(id=request.data['pageId'])

            queue_item: QueueItem = QueueItem(page=page[0], website=website, priority=prio)
            queue_item.save()

            data = serialize("json", [queue_item], fields=('page', 'website', 'status', 'priority', 'created_at'))

            return HttpResponse(data)

        return Response([''])

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_addresses(self, request, version, website_id=None):
        createQueueObjects = []
        website: Website = Website.objects.filter(id=website_id).first()

        if request.data:
            recachePages = Page.objects.filter(website_id=website_id).filter(address__in=request.data.values())

            for page in recachePages:
                queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                createQueueObjects.append(queue_item)

            QueueItem.objects.bulk_create(createQueueObjects)

            return HttpResponse(status=200)

        return HttpResponse(status=404)
