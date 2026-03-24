from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import pickle
from typing import Any, cast
# from .services.autocomplete import AutocompleteService
# from .serializers import AutocompleteRequestSerializer
    
with open('models/autocomplete/malagasy_trigram.pkl', 'rb') as f:
    model = pickle.load(f)
    
class AutocompleteView(APIView):
    
    def predict_next(self, text: str, top_k: int = 5):
        """
        Predit les prochaines suggestions de mots.
        """
        if not hasattr(model, "autocomplete"):
            raise RuntimeError("Le modèle ne supporte pas l'autocomplétion.")
        # On suppose ici que autocomplete peut prendre X en entrée, ou que le modèle nécessite la version vectorisée du texte
        suggestions = model.autocomplete(self, text, top_k)
        return suggestions
        
    def post(self, request):

        data = request.data
        text = data.get('text')
        top_k = data.get('top_k')
        suggestions = self.predict_next(text, top_k)

        # Formater la réponse
        result = [{'word': w, 'prob': p} for w, p in suggestions]
        return Response({'suggestions': result})

# class SentimentCheckView(APIView):
    