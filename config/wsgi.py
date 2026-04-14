import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.info("WSGI: chargement")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from django.core.wsgi import get_wsgi_application
    logging.info("WSGI: appel get_wsgi_application")
    application = get_wsgi_application()
    logging.info("WSGI: application créée")
except Exception as e:
    logging.exception("WSGI: erreur fatale")
    raise