from django.db import models
from django_mysql.models import Model

from seosnap.models import Website


class ExtractField(Model):
    website = models.ForeignKey(Website, related_name='extract_fields', on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    css_selector = models.CharField(max_length=255)
    display = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.css_selector[:30]}'
