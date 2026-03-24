from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        """Précharge tous les modèles .pkl au démarrage du serveur."""
        from .ml_loader import get_models
        get_models()
