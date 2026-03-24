from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import pickle
from typing import Any, cast

from django.conf import settings
# from .services.autocomplete import AutocompleteService
from .serializers import AutocompleteRequestSerializer, SentimentSerializer

MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/autocomplete', 'malagasy_trigram.pkl')
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)


MODEL_PATH_SENTIMENT = os.path.join(settings.BASE_DIR, 'models', 'sentimentCheck', 'sentiment_model.pkl')
with open(MODEL_PATH_SENTIMENT, 'rb') as f:
    sentiment_data = pickle.load(f)

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
    

class SentimentAPIView(APIView):
    # Attributs de classe
    model = sentiment_data['model']
    vectorizer = sentiment_data['vectorizer']
    le = sentiment_data['label_encoder']

    @staticmethod
    def preprocess_text(text: str) -> str:
        # Ici tu peux mettre ton vrai preprocessing
        return text.lower().strip()

    @classmethod
    def predict_sentiment(cls, text: str):
        clean_text = cls.preprocess_text(text)
        X_new = cls.vectorizer.transform([clean_text])
        prediction = cls.model.predict(X_new)
        return cls.le.inverse_transform(prediction)[0]

    def post(self, request):
        serializer = SentimentSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            sentiment = self.predict_sentiment(text)
            return Response({'text': text, 'sentiment': sentiment})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)