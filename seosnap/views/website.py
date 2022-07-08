import os
from datetime import datetime, timedelta

import coreapi
import coreschema
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import viewsets, decorators
from rest_framework.schemas import AutoSchema
from django.core import serializers
from seosnap.serializers import PageSerializer

from seosnap.models import Website, Page
from seosnap.serializers import WebsiteSerializer, WebsiteReportingSerializer


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer


class WebsiteReport(viewsets.ViewSet):
    @decorators.action(detail=True, methods=['get'])
    def get_logging(self, request, version):
        website_ids = []
        if request.query_params.getlist('website_ids'):
            website_ids = request.query_params.getlist('website_ids')

        one_hour_ago = timezone.now() - timedelta(hours=1)
        lastHourUpdated = Page.objects \
            .filter(website_id__in=website_ids) \
            .filter(cache_status='cached') \
            .filter(updated_at__gte=one_hour_ago) \
            .count()

        pages = Page.objects \
            .filter(website_id__in=website_ids) \
            .filter(cache_status='cached') \
            .order_by('-updated_at')[:50]
        pageSerializer = PageSerializer(pages, many=True)

        return JsonResponse({
            "successful_last_hour": lastHourUpdated,
            "last_updated_pages": pageSerializer.data
        })


class WebsiteReportFailure(viewsets.ViewSet):
    serializer_class = WebsiteReportingSerializer
    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "errors",
            location="body",
            schema=coreschema.Array(
                items=coreschema.Object(
                    properties={},
                    title="Error",
                )
            )
        ),
    ])

    @decorators.action(detail=True, methods=['post'])
    def report_failure(self, request, version, website_id=None):
        website: Website = Website.objects.filter(id=website_id).first()
        errors = request.data if isinstance(request.data, list) else []
        message = render_to_string('reporting_email.html', {'errors': errors, 'website': website})

        if not website.notification_sent_date \
                or website.notification_sent_date < timezone.now() - timedelta(seconds=website.notification_cooldown):
            website.notification_sent_date = datetime.now()
            website.save()
            send_mail(
                f'SeoSnap Reporting - {website.name}',
                message,
                os.getenv('ADMIN_EMAIL', 'snaptron@snaptron.nl'),
                [website.notification_email],
                fail_silently=False,
                html_message=message
            )

        return Response([])
