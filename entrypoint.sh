#!/bin/sh
set -eu

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Checking initial superuser..."
python manage.py ensure_superuser

echo "Starting application server..."
exec "$@"
