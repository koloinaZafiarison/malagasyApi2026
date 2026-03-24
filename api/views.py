from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import pickle
from typing import Any, cast

from django.conf import settings
# from .services.autocomplete import AutocompleteService
from .serializers import AutocompleteRequestSerializer

MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/autocomplete', 'malagasy_trigram.pkl')
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)
    
class AutocompleteView(APIView):
    
    def predict_next(self, text: str, top_k: int = 5):
        """
        Predit les prochaines suggestions de mots.
        """
        if not hasattr(model, "autocomplete"):
            raise RuntimeError("Le modèle ne supporte pas l'autocomplétion.")
        suggestions = model.autocomplete(text, top_k)
        return suggestions
        
    def post(self, request):

        data = request.data
        text = data.get('text')
        top_k = data.get('top_k')
        suggestions = self.predict_next(text, top_k)

        # Formater la réponse
        result = [{'word': w, 'prob': p} for w, p in suggestions]
        return Response({'suggestions': result})
    