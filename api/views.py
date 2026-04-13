from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import HttpResponse
import os
import re
import pickle
import ast
from collections import Counter, defaultdict
from typing import Any, cast
from typing import List, Dict
from dataclasses import dataclass
from .serializers import AutocompleteRequestSerializer, SentimentSerializer
from api.services.tts import MalagasyTTS

# ----------------------------
# Chargement des modèles
# ----------------------------
MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/autocomplete/malagasy_trigram.pkl')
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

MODEL_PATH_SENTIMENT = os.path.join(settings.BASE_DIR, 'models', 'sentimentCheck', 'sentiment_model.pkl')
with open(MODEL_PATH_SENTIMENT, 'rb') as f:
    sentiment_data = pickle.load(f)


MODEL_PATH_SENTIMENT = os.path.join(settings.BASE_DIR, 'models/sentimentCheck/sentiment_model.pkl')
with open(MODEL_PATH_SENTIMENT, 'rb') as f:
    sentiment_data = pickle.load(f)

MODEL_PATH_NLP_MLG = os.path.join(settings.BASE_DIR, 'models/nlp-malagasy/modele_nlp_malagasy.pkl')
with open(MODEL_PATH_NLP_MLG, "rb") as f:
    modele = pickle.load(f)

DICTIONNAIRE    = modele["DICTIONNAIRE"]
RACINES_TENY    = modele["RACINES_TENY"]
MOT_VERS_RACINE = modele["MOT_VERS_RACINE"]
DICO_LIST       = modele["DICO_LIST"]
STOPWORDS_MG    = modele["STOPWORDS_MG"]

# ----------------------------
# Fonctions utilitaires
# ----------------------------
def tokeniser(texte: str) -> List[str]:
    """Tokenizer simple du texte malagasy"""
    texte = texte.replace("\u2019", "'").replace("\u2018", "'")
    tokens = []
    for bloc in re.split(r'[\s,;:!?."()\n]+', texte):
        bloc = bloc.strip()
        if not bloc:
            continue
        for partie in bloc.split("-"):
            for sp in partie.split("'"):
                sp = sp.lower().strip().strip("'")
                if len(sp) >= 2:
                    tokens.append(sp)
    return tokens

def est_correct(mot: str) -> bool:
    return mot.lower().strip() in DICTIONNAIRE

def suggerer(mot: str, nb: int = 3) -> List[tuple]:
    from rapidfuzz import process, fuzz
    resultats = process.extract(mot.lower().strip(), DICO_LIST, scorer=fuzz.ratio, limit=nb)
    return [(m, s) for m, s, _ in resultats]

def corriger_texte(texte: str) -> Dict[str, List[tuple]]:
    erreurs = {}
    for mot in set(tokeniser(texte)):
        if mot in STOPWORDS_MG:
            continue
        if not est_correct(mot):
            erreurs[mot] = suggerer(mot)
    return erreurs

@dataclass
class ErreurPhono:
    mot: str
    regle: str
    description: str

REGLES_PHONOTACTIQUES = [
    {"id":"COMB_INTERDIT", "pattern": re.compile(r'nb|mk|dt|bp|sz', re.I), "description":"Combinaison de consonnes inexistante"},
    {"id":"NK_DEBUT", "pattern": re.compile(r'^nk', re.I), "description":"Début de mot par 'nk' interdit"},
    {"id":"LETTRE_ETRANGERE", "pattern": re.compile(r'[cquwx]', re.I), "description":"Lettre absente de l'alphabet malagasy"},
    {"id":"DOUBLE_CONSONNE", "pattern": re.compile(r'([bcdfgjklmnprstvz])\1', re.I), "description":"Double consonne inhabituelle"},
    {"id":"FIN_CONSONNE", "pattern": re.compile(r'[bcdfgjklmprstv]$', re.I), "description":"Fin de mot atypique"},
]

def verifier_phonotactique(mot: str) -> List[ErreurPhono]:
    if mot.lower() in DICTIONNAIRE:
        return []
    erreurs = []
    for regle in REGLES_PHONOTACTIQUES:
        if regle["pattern"].search(mot.strip()):
            erreurs.append(ErreurPhono(mot, regle["id"], regle["description"]))
    return erreurs

def lemmatiser(mot: str) -> Dict[str, str]:
    mot_c = mot.lower().strip()
    if mot_c in MOT_VERS_RACINE:
        return {"racine": MOT_VERS_RACINE[mot_c], "methode": "lookup_direct"}
    if mot_c in RACINES_TENY:
        return {"racine": mot_c, "methode": "racine_directe"}
    return {"racine": mot_c, "methode": "non_trouvé"}

# ----------------------------
# API Views
# ----------------------------
def get_text_from_request(request) -> str:
    """Récupère le texte depuis la requête POST (texte ou text)"""
    return request.data.get('texte') or request.data.get('text', '')


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


class TTSView(APIView):
    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tts = MalagasyTTS()
            audio_bytes = tts.synthesize(text)
            return HttpResponse(audio_bytes, content_type="audio/wav")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SentimentAPIView(APIView):
    model = sentiment_data['model']
    vectorizer = sentiment_data['vectorizer']
    le = sentiment_data['label_encoder']

    @staticmethod
    def preprocess_text(text: str) -> str:
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
            validated_data = cast(dict[str, Any], serializer.validated_data)
            text = str(validated_data["text"])
            sentiment = self.predict_sentiment(text)
            return Response({'text': text, 'sentiment': sentiment})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrthographeAPIView(APIView):
    def post(self, request):
        texte = get_text_from_request(request)
        result = corriger_texte(texte)
        return Response({'texte': texte, 'corrections': result})

class PhonotactiqueAPIView(APIView):
    def post(self, request):
        texte = get_text_from_request(request)
        tokens = tokeniser(texte)
        result = {mot: [e.__dict__ for e in verifier_phonotactique(mot)] for mot in tokens}
        return Response({'texte': texte, 'phonotactique': result})

class LemmatizationAPIView(APIView):
    def post(self, request):
        texte = get_text_from_request(request)
        tokens = tokeniser(texte)
        result = {mot: lemmatiser(mot) for mot in tokens}
        return Response({'texte': texte, 'lemmes': result})
