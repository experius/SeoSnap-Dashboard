import coreapi, coreschema, requests
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

class PageWebsiteList(viewsets.ViewSet, PageNumberPagination):
    @decorators.action(detail=True, methods=['get'])
    def pages(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        allowed = request.user.has_perm('seosnap.view_website', website)
        if not allowed or not website: return Response([])

        if request.GET.get('filter'):
            queryset = list(filter(lambda page: page.address.startswith(request.GET.get('filter')), website.pages.all()))
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

    @decorators.action(detail=True, methods=['get'])
    def sync(self, request, version, website_id=None):
        website = Website.objects.filter(id=website_id).first()
        domain = website.domain

        siteMapUrl = website.sitemap

        # TODO minutes to setting
        doCacheAgain = datetime.now(timezone.utc) - timedelta(minutes=10000)

        # Get sitemap data
        r = requests.get(siteMapUrl)
        root = ET.fromstring(r.text)

        print("start <-")

        # check multiple sitemaps
        # TODO make this way faster...
        rootData = None
        for sitemapMap in root:
            if sitemapMap.tag.endswith("sitemap"):
                for pageData in sitemapMap:
                    if pageData.tag.endswith('loc'):
                        print(pageData.text)
                        request = requests.get(pageData.text)
                        data = ET.fromstring(request.text)

                        if rootData is None:
                            rootData = data
                        else:
                            for url in data:
                                rootData.append(url)
            else:
                rootData = root
                break

        print("start")
        print(len(rootData))

        urlList = []
        for pageSiteMap in rootData:
            url = None
            lastMod = None

            # Get sitemap data
            for pageData in pageSiteMap:
                if pageData.tag.endswith('loc'):
                    url = pageData.text
                    if url.startswith(domain):
                        url = "/" + url[len(domain):]
                    urlList.append(url)

                if pageData.tag.endswith('lastmod'):
                    lastMod = datetime.strptime(pageData.text, '%Y-%m-%dT%H:%M:%S%z')

            if url is not None:

                # check if page is in db
                page = Page.objects.filter(website_id=website_id).filter(address=url).first()
                if page is None:
                    # Url not found in DB
                    # Shoot page in DB and add queue item
                    print("nope <<<-----------------------------------------")
                    print(url)

                    page: Page = Page(address=url, website=website)
                    page.save()

                    queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                    queue_item.save()
                else:
                    # Page found in DB
                    # check last updated for mismatch with SeoSnap and delete

                    if lastMod is not None:
                        # if last mod is longer than X min ago
                        # Or later than page updated at

                        sitemapDiff = page.updated_at - lastMod
                        rendertronDiff = page.updated_at - doCacheAgain
                        if (sitemapDiff.total_seconds() <= 0) or (rendertronDiff.total_seconds() <= 0):
                            print("REDO <<<<----------")
                            print(page.address)

                            queue_item_found = QueueItem.objects.filter(page=page).filter(status="unscheduled").first()
                            if queue_item_found is None:
                                queue_item: QueueItem = QueueItem(page=page, website=website, priority=10000)
                                queue_item.save()
                    else:
                        print("no last modddddddd <<<< =-----------")
                        print(page.address)
            else:
                print("errorrrrrrrrrrrrrrrrrrrrr")

        deletablePages = Page.objects.filter(website_id=website_id).exclude(address__in=urlList)
        for page in deletablePages:
            head, sep, tail = page.address.partition('?')
            queue_item_found = QueueItem.objects.filter(page=page).filter(status="unscheduled").first()

            if head not in urlList and queue_item_found is None:
                QueueItem.objects.filter(page=page).delete()
                page.delete()

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

        queryset = list(filter(lambda page: any(' ' + word + ' ' in ' ' + page.x_magento_tags.decode('UTF-8') + ' ' for word in tags.split(' ')), website.pages.all()))
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