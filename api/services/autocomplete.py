# # api/services/autocomplete.py
# import pickle
# import os
# import re
# from collections import defaultdict, Counter
# from typing import Any, List, Tuple, Optional
# from django.conf import settings


# class AutocompleteService:
#     _instance = None
#     model : Any

#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             # Chargement du modèle lors de la création de l'instance unique
#             model_path = os.path.join(settings.BASE_DIR, 'models', 'autocomplete', 'malagasy_trigram.pkl')
#             with open(model_path, 'rb') as f:
#                 loaded = pickle.load(f)
#                 model = cls._coerce_model(loaded)
#                 # On utilise setattr pour éviter un faux positif de linter concernant l'attribut dynamique 'model'
#                 object.__setattr__(cls._instance, "model", model)
#         return cls._instance

#     @staticmethod
#     def _coerce_model(loaded_model):
#         """Accepte un objet modèle direct ou un état dict sérialisé."""
#         if hasattr(loaded_model, "autocomplete"):
#             return loaded_model
#         if isinstance(loaded_model, dict):
#             return MalagasyNGramPredictor.from_state(loaded_model)
#         raise TypeError(
#             f"Format de modèle non supporté: {type(loaded_model).__name__}. "
#             "Attendu: objet avec méthode autocomplete() ou dict sérialisé."
#         )

#     def get_suggestions(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
#         # Vérifie que l'instance possède bien l'attribut 'model'
#         if not hasattr(self, "model"):
#             raise RuntimeError("Le modèle n'est pas chargé dans l'instance AutocompleteService.")
#         if self.model is None:
#             raise RuntimeError("Le modèle d'autocomplétion est vide.")
#         return self.model.autocomplete(text, top_k)