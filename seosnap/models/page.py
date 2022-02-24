from django.db import models
from django_mysql.models import Model

from seosnap.utils.JSONField import JSONField
from seosnap.models import Website


class Page(Model):
    website = models.ForeignKey(Website, related_name='pages', on_delete=models.CASCADE)

    address = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, null=True, default=None)
    status_code = models.IntegerField(null=True, default=None)
    extract_fields = JSONField(default=dict)
    x_magento_tags = models.BinaryField(null=True, editable=True)

    cache_status = models.CharField(max_length=64, choices=[
        ('cached', 'Cached'),
        ('not-cached', 'Not Cached')
    ], default='not-cached')
    cached_at = models.DateTimeField(null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __setattr__(self, attrname, val):
        setter_func = 'setter_' + attrname

        if attrname in self.__dict__ and callable(getattr(self, setter_func, None)):
            super(Page, self).__setattr__(attrname, getattr(self, setter_func)(val))
        elif attrname == "x_magento_tags":
            super(Page, self).__setattr__(attrname, getattr(self, setter_func)(val))
        else:
            super(Page, self).__setattr__(attrname, val)

    def setter_x_magento_tags(self, value):
        if type(value) is bytes:
            return value
        return value.encode()

    def setter_id(self, value):
        return value

    def __str__(self):
        return f'{self.address}'

    def get_extract_field(self, name):
        return self.extract_fields.get(name, None)
