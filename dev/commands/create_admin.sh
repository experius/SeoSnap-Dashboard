#!/bin/sh

python manage.py shell << EOF
from django.contrib.auth.models import User
print("Creating user $ADMIN_NAME")
if not User.objects.filter(username="$ADMIN_NAME").exists():
  User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$ADMIN_PASS')
EOF
