# Load env vars
# shellcheck disable=SC2046
export $(egrep -v '^#' .env | xargs)

./manage.py migrate

echo "Admin: $ADMIN_NAME"
export DJANGO_SUPERUSER_PASSWORD="$ADMIN_PASS"
./manage.py createsuperuser --username "$ADMIN_NAME" --email "$ADMIN_EMAIL" --no-input

python manage.py runserver 0.0.0.0:80