from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
import pickle
import ast
import re
from collections import Counter, defaultdict
from typing import Any, cast
from .serializers import AutocompleteRequestSerializer

MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "autocomplete", "malagasy_trigram.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


class MalagasyNGramPredictor:
    """
    Reconstitution légère du modèle entraîné dans le notebook.
    Charge le format sérialisé avec clés: n, smoothing, vocab, ngrams, etc.
    """

    def __init__(self):
        self.n = 3
        self.smoothing = 1.0
        self.vocab: set[str] = set()
        self.vocab_size = 0
        self.ngrams: defaultdict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        self.START = "<S>"
        self.END = "</S>"
        self.UNK = "<UNK>"

    @staticmethod
    def from_state(state: dict[str, Any]) -> "MalagasyNGramPredictor":
        predictor = MalagasyNGramPredictor()
        predictor.n = int(state.get("n", 3))
        predictor.smoothing = float(state.get("smoothing", 1.0))
        predictor.vocab = set(state.get("vocab", []))
        predictor.vocab_size = int(state.get("vocab_size", len(predictor.vocab)))
        predictor.START = str(state.get("START", "<S>"))
        predictor.END = str(state.get("END", "</S>"))
        predictor.UNK = str(state.get("UNK", "<UNK>"))

        serialized_ngrams = state.get("ngrams", {})
        if isinstance(serialized_ngrams, dict):
            for k, v in serialized_ngrams.items():
                context = ast.literal_eval(k) if isinstance(k, str) else tuple(k)
                predictor.ngrams[tuple(context)] = Counter(v)

        return predictor

    def tokenize(self, text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r"[a-zA-Zàâäéèêëïîôöùûüçñ']+", text)
        tokens = [t for t in tokens if len(t) > 1 or t in ["a", "i", "ny"]]
        return tokens

    def predict(self, context_tokens: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        if len(context_tokens) > self.n - 1:
            context_tokens = context_tokens[-(self.n - 1):]
        elif len(context_tokens) < self.n - 1:
            context_tokens = [self.START] * (self.n - 1 - len(context_tokens)) + context_tokens

        context_tokens = [t if t in self.vocab else self.UNK for t in context_tokens]
        context = tuple(context_tokens)

        total_context = sum(self.ngrams[context].values())
        denom = total_context + self.smoothing * self.vocab_size
        if denom <= 0:
            return []

        probas: list[tuple[str, float]] = []
        for word in self.vocab:
            if word in [self.START, self.END, self.UNK]:
                continue
            count_w = self.ngrams[context].get(word, 0)
            prob = (count_w + self.smoothing) / denom
            probas.append((word, prob))

        probas.sort(key=lambda x: -x[1])
        return probas[:top_k]

    def autocomplete(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        tokens = self.tokenize(text)
        if not tokens:
            return []
        return self.predict(tokens, top_k)


if isinstance(model, dict) and {"n", "vocab", "ngrams"}.issubset(model.keys()):
    model = MalagasyNGramPredictor.from_state(model)


class AutocompleteView(APIView):

    @staticmethod
    def _autocomplete_from_dict(ngram_data: dict[str, dict[str, int]], text: str, top_k: int = 5):
        """
        Fallback pour les modèles sérialisés en dictionnaire:
        {mot_contexte: {mot_suivant: frequence}}.
        """
        last_word = (text or "").strip().split()
        if not last_word:
            return []

        context = last_word[-1].lower()
        next_words = ngram_data.get(context, {})
        if not next_words:
            return []

        total = sum(next_words.values())
        if total <= 0:
            return []

        ranked = sorted(next_words.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [(word, freq / total) for word, freq in ranked]

    def predict_next(self, text: str, top_k: int = 5):
        """
        Predit les prochaines suggestions de mots.
        """
        if hasattr(model, "autocomplete"):
            return model.autocomplete(text, top_k)

        raise RuntimeError("Format de modèle non supporté pour l'autocomplétion.")

    def post(self, request):
        serializer = AutocompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)

        text = str(validated_data["text"])
        top_k = int(validated_data.get("top_k", 5))
        suggestions = self.predict_next(text, top_k)

        # Formater la réponse
        result = [{"word": w, "prob": p} for w, p in suggestions]
        return Response({"suggestions": result}, status=status.HTTP_200_OK)

# class SentimentCheckView(APIView):
    