#!/bin/bash
set -e

echo "[start] collectstatic"
python manage.py collectstatic --noinput

echo "[start] migrate"
python manage.py migrate --noinput

echo "[start] gunicorn"
exec gunicorn playground_server.wsgi:application \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers 2 \
  --threads 4 \
  --timeout 120
