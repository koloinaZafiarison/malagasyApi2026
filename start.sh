#!/bin/bash
set -x  # Affiche chaque commande
set -e  # Stoppe le script à la première erreur

echo "=== Démarrage ==="
echo "PORT = $PORT"

echo "=== Migration ==="
python manage.py migrate --noinput --verbosity 3

echo "=== Collectstatic ==="
python manage.py collectstatic --noinput

echo "=== Gunicorn ==="
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 1 --worker-class sync --log-level debug --access-logfile - --error-logfile -