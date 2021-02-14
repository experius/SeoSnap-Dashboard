import django
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_mysql.models import Model, QuerySet
from django.db.models.expressions import RawSQL

from urllib.parse import urlparse

import seosnap


class Website(Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    sitemap = models.CharField(max_length=255, null=True, default=None)

    cache_updated_at = models.DateTimeField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notification_email = models.CharField(max_length=255, default='')
    notification_failure_rate = models.IntegerField(default=10)
    notification_sent_date = models.DateTimeField(default=django.utils.timezone.now)
    notification_cooldown = models.IntegerField(default=3600)

    def __str__(self):
        return f'{self.name} - {self.domain}'

    def get_extract_fields(self):
        return [field for field in self.extract_fields.values_list('name', flat=True)]

    def get_display_extract_fields(self):
        return [field for field in self.extract_fields.filter(display=True).values_list('name', flat=True)]

    def get_url(self, path):
        if isinstance(path, seosnap.models.Page): path = path.address
        uri = urlparse(self.domain)
        root_domain = f'{uri.scheme}://{uri.netloc}'
        return root_domain + path