#!/bin/bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 1 --worker-class sync --log-level debug --access-logfile - --error-logfile -