from django.db import models
from django_mysql.models import Model

from seosnap.models import Page, Website


class QueueItem(Model):
    page = models.ForeignKey(Page, related_name='queue_items', on_delete=models.CASCADE)
    website = models.ForeignKey(Website, related_name='queue_items', on_delete=models.CASCADE)

    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=[
        ('unscheduled', 'Unscheduled'),
        ('scheduled', 'Scheduled'),
        ('completed', 'completed'),
        ('failed', 'Failed'),
    ], default='unscheduled')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'QueueItem - {self.page}'
