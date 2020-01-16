from django.db import models
from django_mysql.models import Model

from seosnap.utils.JSONField import JSONField


class Website(Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.domain}'


class ExtractField(Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    css_selector = models.CharField(max_length=255)
    display = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.css_selector[:30]}'


class Page(Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)

    address = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, null=True, default=None)
    status_code = models.IntegerField(null=True, default=None)
    extract_fields = JSONField(default=dict)

    cache_status = models.CharField(max_length=64, choices=[
        ('cached', 'Cached'),
        ('not-cached', 'Not Cached')
    ], default='not-cached')
    cached_at = models.DateTimeField(null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.address}'
