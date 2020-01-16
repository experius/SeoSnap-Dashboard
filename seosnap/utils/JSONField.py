import django_mysql
from django.db import models
from django.db.models.lookups import IContains


class JSONIContains(IContains):
    def process_lhs(self, compiler, connection, lhs=None):
        lhs = lhs or self.lhs
        to_add = compiler.compile(lhs)
        to_add = ('%s COLLATE utf8mb4_unicode_ci ' % to_add[0], to_add[1])
        return to_add


class JSONField(django_mysql.models.JSONField):
    def get_lookup(self, lookup_name):
        # Have to 'unregister' some incompatible lookups
        if lookup_name in {
            'range', 'in', 'iexact', 'startswith',
            'istartswith', 'endswith', 'iendswith', 'search', 'regex', 'iregex'
        }:
            raise NotImplementedError(
                "Lookup '{}' doesn't work with JSONField".format(lookup_name)
            )
        return super(models.Field, self).get_lookup(lookup_name)


JSONField.register_lookup(JSONIContains)
