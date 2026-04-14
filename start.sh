#!/bin/bash
echo "Running migrations..."
python manage.py migrate --noinput
echo "Collecting static..."
python manage.py collectstatic --noinput
echo "Starting Gunicorn with debug logs..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 1 --worker-class sync --log-level debug --access-logfile - --error-logfile -