# Load env vars
if [ -z ${var+x} ]; then
  # shellcheck disable=SC2046
  export $(egrep -v '^#' .env | xargs)
fi

python manage.py migrate

echo "Admin: $ADMIN_NAME"
export DJANGO_SUPERUSER_PASSWORD="$ADMIN_PASS"
python manage.py createsuperuser --username "$ADMIN_NAME" --email "$ADMIN_EMAIL" --no-input

python manage.py runserver 0.0.0.0:8080
