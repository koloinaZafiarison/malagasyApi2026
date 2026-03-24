"""
ml_loader.py
------------
Charge tous les modèles .pkl UNE SEULE FOIS au démarrage du serveur
via le pattern Singleton. Les views accèdent aux modèles via get_models().

Structure attendue du dossier ml_models/ :
    ml_models/
    ├── spell_checker.pkl       # dict ou objet avec attribut 'dictionary' (set de mots)
    ├── autocomplete.pkl        # dict de bigrammes/trigrammes {mot: {suivant: freq}}
    ├── lemmatizer.pkl          # dict {forme_fléchie: {root, prefix, suffix}}
    ├── sentiment.pkl           # dict avec 'positive_words' et 'negative_words' (lists)
    ├── translator.pkl          # dict {mot_mg: {fr: traduction, en: traduction}}
    └── ner.pkl                 # dict avec 'cities', 'persons', 'organizations' (lists)

Si un fichier .pkl est absent, le loader utilise automatiquement
un fallback vide pour ne pas bloquer le démarrage.
"""

import pickle
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Singleton qui charge et expose tous les modèles ML."""

    _instance = None
    _models: dict = {}
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_all(self):
        """Charge tous les .pkl depuis MODELS_DIR. Appelé une fois au démarrage."""
        if self._loaded:
            return

        models_dir: Path = settings.MODELS_DIR
        models_dir.mkdir(parents=True, exist_ok=True)

        model_files = {
            'spell_checker': 'spell_checker.pkl',
            'autocomplete':  'autocomplete.pkl',
            'lemmatizer':    'lemmatizer.pkl',
            'sentiment':     'sentiment.pkl',
            'translator':    'translator.pkl',
            'ner':           'ner.pkl',
        }

        for key, filename in model_files.items():
            path = models_dir / filename
            if path.exists():
                try:
                    with open(path, 'rb') as f:
                        self._models[key] = pickle.load(f)
                    logger.info(f"[ML] Modèle chargé : {filename}")
                except Exception as e:
                    logger.error(f"[ML] Erreur chargement {filename} : {e}")
                    self._models[key] = self._get_fallback(key)
            else:
                logger.warning(f"[ML] Fichier manquant : {filename} — fallback activé")
                self._models[key] = self._get_fallback(key)

        self._loaded = True
        logger.info("[ML] Tous les modèles sont prêts.")

    def get(self, key: str):
        """Retourne un modèle par clé."""
        if not self._loaded:
            self.load_all()
        return self._models.get(key, self._get_fallback(key))

    def reload(self, key: str):
        """Recharge un modèle spécifique (utile après mise à jour d'un .pkl)."""
        models_dir: Path = settings.MODELS_DIR
        filename_map = {
            'spell_checker': 'spell_checker.pkl',
            'autocomplete':  'autocomplete.pkl',
            'lemmatizer':    'lemmatizer.pkl',
            'sentiment':     'sentiment.pkl',
            'translator':    'translator.pkl',
            'ner':           'ner.pkl',
        }
        filename = filename_map.get(key)
        if not filename:
            return False
        path = models_dir / filename
        if path.exists():
            with open(path, 'rb') as f:
                self._models[key] = pickle.load(f)
            logger.info(f"[ML] Modèle rechargé : {filename}")
            return True
        return False

    @staticmethod
    def _get_fallback(key: str):
        """Retourne une structure vide cohérente pour chaque modèle."""
        fallbacks = {
            'spell_checker': {'dictionary': set()},
            'autocomplete':  {},
            'lemmatizer':    {},
            'sentiment': {
                'positive_words': [],
                'negative_words': [],
            },
            'translator':    {},
            'ner': {
                'cities':        [],
                'persons':       [],
                'organizations': [],
            },
        }
        return fallbacks.get(key, {})


# Instance globale — importée par les views
registry = ModelRegistry()


def get_models() -> ModelRegistry:
    """Point d'entrée unique pour accéder aux modèles dans les views."""
    registry.load_all()
    return registry
