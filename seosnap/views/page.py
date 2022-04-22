import coreapi, coreschema, requests, xmltodict
import xml.etree.ElementTree as ET
from django.db import transaction
from rest_framework import viewsets, decorators
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from datetime import datetime, timedelta, timezone

from seosnap.models import Page, Website, QueueItem
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

    def _getSitemapData(self, website: Website, sitemapUrl):
        r = requests.get(sitemapUrl)
        rootDict = xmltodict.parse(r.text)
        data = rootDict['urlset']['url']

        for i, d in enumerate(data):
            if d['loc'].startswith(website.domain):
                data[i]['loc'] = "/" + d['loc'][len(website.domain):]

            if "lastmod" in d:
                data[i]['lastmod'] = datetime.strptime(d['lastmod'], '%Y-%m-%dT%H:%M:%S%z')
            else:
                data[i]['lastmod'] = None

        return data

    def _getSitemapUrls(self, website: Website):
        r = requests.get(website.sitemap)
        rootDict = xmltodict.parse(r.text)

        urls = []
        if "urlset" in rootDict:
            urls = rootDict['urlset']['url']

            for i, d in enumerate(urls):
                if d['loc'].startswith(website.domain):
                    urls[i]['loc'] = "/" + d['loc'][len(website.domain):]

                if "lastmod" in d:
                    urls[i]['lastmod'] = datetime.strptime(d['lastmod'], '%Y-%m-%dT%H:%M:%S%z')
                else:
                    urls[i]['lastmod'] = None

        if "sitemapindex" in rootDict:
            threads = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                for sitemap in rootDict['sitemapindex']['sitemap']:
                    threads.append(executor.submit(self._getSitemapData, website, sitemap['loc']))

                for task in as_completed(threads):
                    print("sitemap loaded")
                    result = task.result()
                    urls.extend(result)

        return urls

    def _multiThreadedPageSync(self, website_id, website, urlsData, doCacheAgain):
        print("start: _multiThreadedPageSync")
        createQueueObjects = []
        urlsList = set()
        count = 0

        for urlData in urlsData:
            urlsList.add(urlData['loc'])

        existingPages = list(Page.objects.filter(website_id=website_id).filter(address__in=urlsList).values_list('address', 'updated_at'))
        addresses = Page.objects.values_list('address', flat=True)

        for urlData in urlsData:

            if urlData['loc'] in addresses:
                urlsList.remove(urlData['loc'])

                if urlData['lastmod'] is not None:
                    # print(type(existingPages))
                    for page in existingPages:

                        if page[0] == urlData['loc']:
                            # if last mod is longer than X min ago
                            # Or later than page updated at
                            # [1] => updated_at

                            sitemapDiff = page[1] - urlData['lastmod']
                            rendertronDiff = page[1] - doCacheAgain
                            if (sitemapDiff.total_seconds() <= 0) or (rendertronDiff.total_seconds() <= 0):
                                print("do queue again")

                                queue_item_found = QueueItem.objects.filter(page=page).filter(
                                    status="unscheduled").first()
                                if queue_item_found is None:
                                    queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                                    createQueueObjects.append(queue_item)
                else:
                    print("No last mod <----")
                    print(urlData['loc'])

        createPageObjects = []

        print("HOII <------")
        print(len(urlsData))
        print(len(urlsList))
        print(count)
        for url in urlsList:
            # print(" ---- start --- ")
            print("create: " + str(url))
            # print(url in addresses)
            # print(" ---- END --- ")
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
        urlsData = self._getSitemapUrls(website)
        doCacheAgain = datetime.now(timezone.utc) - timedelta(minutes=10000)

        print("-- overview --")
        print("total url count: " + str(len(urlsData)))
        print("-- start sync --")

        size = 500
        for i in range(0, len(urlsData), size):
            data = urlsData[i:i + size]
            self._multiThreadedPageSync(website_id, website, data, doCacheAgain)

        # threads = []
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     for i in range(0, len(urlsData), size):
        #         data = urlsData[i:i + size]
        #         threads.append(executor.submit(self._multiThreadedPageSync, website_id, website, data, doCacheAgain))
        #
        #     for task in as_completed(threads):
        #         print("TASK DONE")

        print("-- start delete --")

        urlList = map(lambda x: x["loc"], urlsData)
        deletablePages = Page.objects.filter(website_id=website_id).exclude(address__in=urlList) \
            .exclude(id__in=QueueItem.objects.filter(status="unscheduled").values('page_id'))

        for page in deletablePages:
            head, sep, tail = page.address.partition('?')

            if head not in urlList:
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

        queryset = list(filter(lambda page: any(
            ' ' + word + ' ' in ' ' + page.x_magento_tags.decode('UTF-8') + ' ' for word in tags.split(' ')),
                               website.pages.all()))
        # if any(word in 'some one long two phrase three' for word in list_):

        # Length of queryset
        print(len(queryset))

        # All pages
        print('xx')
        print(request)
        for page in queryset:

            pageFound = QueueItem.objects.filter(page=page).filter(status="unscheduled").first()

            if pageFound is None:
                queue_item: QueueItem = QueueItem(page=page, website=website, priority=request.data['priority'])
                queue_item.save()

        return HttpResponse(status=200)

    @decorators.action(detail=True, methods=['post'])
    def cache_redo_website(self, request, version, website_id=None):
        print(" --- start request ---")
        print("test")

        website: Website = Website.objects.filter(id=website_id).first()
        print("website")
        print(website)

        print("request")
        print(request)
        print(request.data)
        print(request.data['pageId'])

        if request.data['pageId']:
            print('1')
            page: Page = website.pages.filter(id=request.data['pageId'])
            print(page)
            print(page[0])

            print('2')
            queue_item: QueueItem = QueueItem(page=page[0], website=website, priority=10000)

            print('3')
            queue_item.save()
            print(len(page))
            print(queue_item)

            data = serialize("json", [queue_item], fields=('page', 'website', 'status', 'priority', 'created_at'))

            print('4')

            return HttpResponse(data)

        # Todo exception if no page
        return Response([''])
