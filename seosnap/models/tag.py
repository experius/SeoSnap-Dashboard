from django.db import models
from django_mysql.models import Model


class Tag(Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'tag - {self.name}'
