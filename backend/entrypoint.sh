#!/bin/sh
set -e

echo "==> Migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Creating superuser (skipped if exists)..."
python manage.py create_superuser || true

echo "==> Seeding skills from CSV (skipped if already seeded)..."
python manage.py seed_skills || true

echo "==> Starting gunicorn (ASGI + uvicorn workers)..."
exec gunicorn config.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${GUNICORN_LOG_LEVEL:-info}
