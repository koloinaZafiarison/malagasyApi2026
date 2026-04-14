#!/bin/bash
set -e  # arrête le script en cas d'erreur
set -x  # affiche chaque commande exécutée

echo "=== 1. Migration ==="
python manage.py migrate --noinput

echo "=== 2. Collectstatic ==="
python manage.py collectstatic --noinput

echo "=== 3. Démarrage Gunicorn ==="
# Redirige stdout et stderr vers la sortie standard
gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --workers 1 \
    --threads 1 \
    --worker-class sync \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance

# Si Gunicorn échoue, le script s'arrête avec set -e