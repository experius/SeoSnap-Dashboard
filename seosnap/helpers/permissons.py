from django.contrib.auth.models import User
from django_mysql.models import QuerySet
from django.db import connection


def get_allowed_websites(user: User, permission='view_website'):
    if user.is_superuser: return []

    with connection.cursor() as cursor:
        select_permission = 'SELECT id FROM auth_permission aug WHERE aug.codename = %s'
        select_groups = 'SELECT id FROM auth_user_groups aug WHERE aug.user_id = %s'
        cursor.execute(f'''
          SELECT guop.object_pk FROM guardian_userobjectpermission guop
          JOIN django_content_type dct ON dct.id = guop.content_type_id AND model = 'website'
          WHERE guop.permission_id IN ({select_permission}) AND guop.user_id = %s
          UNION
          SELECT ggop.object_pk FROM guardian_groupobjectpermission ggop
          JOIN django_content_type dct ON dct.id = ggop.content_type_id AND model = 'website'
          WHERE ggop.permission_id IN ({select_permission}) AND ggop.group_id in ({select_groups})
        ''', (permission, user.id, permission, user.id))

        return [row[0] for row in cursor.fetchall()]


def filter_permitted_websites(qs: QuerySet, user: User, permission='view_website'):
    if user.is_superuser: return qs

    allowed_website_ids = get_allowed_websites(user, permission)
    return qs.filter(id__in=allowed_website_ids)
