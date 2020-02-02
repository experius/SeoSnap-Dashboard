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


def website_add_permission_filter(qs, permission, user: AbstractUser):
    if user.is_superuser: return qs

    select_permission = 'SELECT id FROM auth_permission aug WHERE aug.codename = %s'
    select_groups = 'SELECT id FROM auth_user_groups aug WHERE aug.user_id = %s'
    qs: QuerySet = qs.filter(id__in=RawSQL(f'''
        SELECT guop.object_pk FROM guardian_userobjectpermission guop
        JOIN django_content_type dct ON dct.id = guop.content_type_id AND model = 'website'
        WHERE guop.permission_id IN ({select_permission}) AND guop.user_id = %s
        UNION
        SELECT ggop.object_pk FROM guardian_groupobjectpermission ggop
        JOIN django_content_type dct ON dct.id = ggop.content_type_id AND model = 'website'
        WHERE ggop.permission_id IN ({select_permission}) AND ggop.group_id in ({select_groups})
    ''', (permission, user.id, permission, user.id)))
    return qs
