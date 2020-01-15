from django.db import models
from django_mysql.models import JSONField, Model


class Website(Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Page(Model):
    address = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    status_code = models.IntegerField(null=True, default=None)
    extract_fields = JSONField(default=dict)

    cache_status = models.CharField(max_length=64, choices=[
        ('cached', 'Cached'),
        ('not-cached', 'Not Cached')
    ], default='cached')
    cached_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
