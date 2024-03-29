import coreapi, coreschema, requests, xmltodict
import xml.etree.ElementTree as ET
from django.db import transaction
from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from datetime import datetime, timedelta, timezone
from django.db.models import Q

from seosnap.models import Page, Website, QueueItem, Tag
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

        existingPages = Page.objects.filter(website_id=website_id).filter(address__in=urlsList)
        addresses = Page.objects.values_list('address', flat=True)

        for urlData in urlsData:

            if urlData['loc'] in addresses:
                if urlData['loc'] in urlsList:
                    urlsList.remove(urlData['loc'])

                # print(type(existingPages))
                for page in existingPages:

                    if page.address == urlData['loc'] and urlData['lastmod'] is not None:
                        # if last mod is longer than X min ago
                        # Or later than page updated at
                        # [1] => updated_at

                        sitemapDiff = page.updated_at - urlData['lastmod']
                        rendertronDiff = page.updated_at - doCacheAgain
                        if (sitemapDiff.total_seconds() <= 0) or (rendertronDiff.total_seconds() <= 0):

                            queue_item_found = QueueItem.objects.filter(page=page).filter(status="unscheduled").first()
                            if queue_item_found is None:
                                queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                                createQueueObjects.append(queue_item)

        createPageObjects = []

        print("Create count <------")
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

        print("-- fully deleted --")

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

        tagsString = ""
        for item in items:
            item = {k: item[k] for k in allowed_fields if k in item}
            if item['address'] in existing:
                page = existing[item['address']]
                for k, v in item.items(): setattr(page, k, v)
            else:
                existing[item['address']] = Page(**item)
            tagsString = tagsString + " " + item['x_magento_tags'].strip()

        tagsArrayFull = set(tagsString.strip().split(" "))

        createTagObjects = []
        singleTagArray = []
        #Split all x_magento_tags blocks into their individual tags
        for tagString in tagsArrayFull:
            tagStringArray = tagString.strip().split(",")
            singleTagArray.extend(tagStringArray)
        #remove duplicates by changing list to set
        singleTagArray = set(singleTagArray)
        existingTags = Tag.objects.filter(name__in=singleTagArray).values_list('name', flat=True)
        for singleTag in singleTagArray:
             if singleTag not in existingTags:
                tag = Tag(name=singleTag)
                createTagObjects.append(tag)
        Tag.objects.bulk_create(createTagObjects)

        with transaction.atomic():
            cache_updated_at = website.cache_updated_at
            for page in existing.values():
                page.website_id = website_id

                tagsArray = page.x_magento_tags.strip().split(' ')
                pageArray = [];
                #Split all x_magento_tags blocks into their individual tags
                for tags in tagsArray:
                    tagStringArray = tags.strip().split(",")
                    pageArray.extend(tagStringArray)
                pageArray = set(pageArray);
                existingTagObjects = Tag.objects.filter(name__in=pageArray)
                #Create new page object if it doesn't exist, assiging tags requires object to exist
                if not page.id:
                    page.save()
                page.tags.set(existingTagObjects)

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
            query |= Q(tags__name=tag)

        pages = website.pages.filter(query)

        createQueueObjects = []

        itemsFound = QueueItem.objects.filter(page__in=pages).filter(status="unscheduled").values_list('page_id', flat=True)
        for p in pages:
            if p.id not in itemsFound:
                queue_item: QueueItem = QueueItem(page=p, website=website, priority=request.data['priority'])
                createQueueObjects.append(queue_item)

        QueueItem.objects.bulk_create(createQueueObjects)

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_website(self, request, version):
        if request.data['pageId']:
            prio = 10000
            if request.data['priority']:
                prio = 1

            page: Page = Page.objects.filter(id=request.data['pageId'])

            queue_item: QueueItem = QueueItem(page=page[0], website=page[0].website, priority=prio)
            queue_item.save()

            data = serialize("json", [queue_item], fields=('page', 'website', 'status', 'priority', 'created_at'))

            return HttpResponse(data)

        return Response([''])

    @decorators.action(detail=True, methods=['post'])
    def multiple_cache_redo_website(self, request, version):
        pages = Page.objects.filter(id__in=request.data.values())

        for page in pages:
            queue_item: QueueItem = QueueItem(page=page, website=page.website, priority=100)
            queue_item.save()

        return HttpResponse(status=200)



class Pages(viewsets.ViewSet, PageNumberPagination):

    @decorators.action(detail=True, methods=['get'])
    def get_pages(self, request, version):
        website_ids = []
        if request.query_params.getlist('website_ids'):
            website_ids = request.query_params.getlist('website_ids')

        if request.GET.get('filter'):
            queryset = list(filter(lambda page: page.address.startswith(request.GET.get('filter')), Page.objects.filter(website_id__in=website_ids).all()))
        else:
            queryset = Page.objects.filter(website_id__in=website_ids).all()

        if request.GET.get('limit'):
            self.page_size = request.GET.get('limit')

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = PageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PageSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_tag(self, request, version):
        website_ids = []
        tags = request.data['tags']
        if request.query_params.getlist('website_ids'):
            website_ids = request.query_params.getlist('website_ids')

        query = Q()
        for tag in tags.split(' '):
            query |= Q(tags__name=tag)

        pages = Page.objects.filter(website_id__in=website_ids).filter(query)
        createQueueObjects = []
        itemsFound = QueueItem.objects.filter(page__in=pages).filter(status="unscheduled").values_list('page_id',
                                                                                                       flat=True)
        for p in pages:
            if p.id not in itemsFound:
                queue_item: QueueItem = QueueItem(page=p, website=p.website_id, priority=request.data['priority'])
                createQueueObjects.append(queue_item)

        QueueItem.objects.bulk_create(createQueueObjects)

        return HttpResponse(status=200)
