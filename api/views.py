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
from .services.tts import MalagasyTTS
import requests

# ----------------------------
# Fonctions de chargement paresseux des modèles
# ----------------------------

BASE_URL = "https://huggingface.co/DisMisa/sentiment-check/resolve/main"

def _load_pickle_model(filename: str):
    """Télécharge et charge un modèle pickle depuis Hugging Face"""
    url = f"{BASE_URL}/{filename}"
    response = requests.get(url)
    response.raise_for_status()
    return pickle.loads(response.content)

# Variables globales (initialisées à None)
_trigram_model = None
_sentiment_data = None
_nlp_model = None

def get_trigram_model():
    global _trigram_model
    if _trigram_model is None:
        _trigram_model = _load_pickle_model("malagasy_trigram.pkl")
        # Conversion si nécessaire
        if isinstance(_trigram_model, dict) and {"n", "vocab", "ngrams"}.issubset(_trigram_model.keys()):
            _trigram_model = MalagasyNGramPredictor.from_state(_trigram_model)
    return _trigram_model

def get_sentiment_data():
    global _sentiment_data
    if _sentiment_data is None:
        _sentiment_data = _load_pickle_model("sentiment_model.pkl")
    return _sentiment_data

def get_nlp_model():
    global _nlp_model
    if _nlp_model is None:
        _nlp_model = _load_pickle_model("modele_nlp_malagasy.pkl")
    return _nlp_model

# Accès aux sous-composants NLP (via des propriétés ou fonctions)
def get_dictionnaire():
    return get_nlp_model()["DICTIONNAIRE"]

def get_racines_teny():
    return get_nlp_model()["RACINES_TENY"]

def get_mot_vers_racine():
    return get_nlp_model()["MOT_VERS_RACINE"]

def get_dico_list():
    return get_nlp_model()["DICO_LIST"]

def get_stopwords_mg():
    return get_nlp_model()["STOPWORDS_MG"]

# ----------------------------
# Fonctions utilitaires (adaptées avec chargement paresseux)
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
    return mot.lower().strip() in get_dictionnaire()

def suggerer(mot: str, nb: int = 3) -> List[tuple]:
    from rapidfuzz import process, fuzz
    dico = get_dico_list()
    resultats = process.extract(mot.lower().strip(), dico, scorer=fuzz.ratio, limit=nb)
    return [(m, s) for m, s, _ in resultats]

def corriger_texte(texte: str) -> Dict[str, List[tuple]]:
    stopwords = get_stopwords_mg()
    erreurs = {}
    for mot in set(tokeniser(texte)):
        if mot in stopwords:
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
    if mot.lower() in get_dictionnaire():
        return []
    erreurs = []
    for regle in REGLES_PHONOTACTIQUES:
        if regle["pattern"].search(mot.strip()):
            erreurs.append(ErreurPhono(mot, regle["id"], regle["description"]))
    return erreurs

def lemmatiser(mot: str) -> Dict[str, str]:
    mot_c = mot.lower().strip()
    mot_vers_racine = get_mot_vers_racine()
    racines_teny = get_racines_teny()
    if mot_c in mot_vers_racine:
        return {"racine": mot_vers_racine[mot_c], "methode": "lookup_direct"}
    if mot_c in racines_teny:
        return {"racine": mot_c, "methode": "racine_directe"}
    return {"racine": mot_c, "methode": "non_trouvé"}

# ----------------------------
# Classe MalagasyNGramPredictor (inchangée)
# ----------------------------
class MalagasyNGramPredictor:
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

# ----------------------------
# Vues API (avec chargement paresseux)
# ----------------------------
def get_text_from_request(request) -> str:
    return request.data.get('texte') or request.data.get('text', '')

class AutocompleteView(APIView):
    def predict_next(self, text: str, top_k: int = 5):
        model = get_trigram_model()
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
    @property
    def sentiment_data(self):
        return get_sentiment_data()

    def post(self, request):
        serializer = SentimentSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = cast(dict[str, Any], serializer.validated_data)
            text = str(validated_data["text"])
            data = self.sentiment_data
            clean_text = text.lower().strip()
            X_new = data['vectorizer'].transform([clean_text])
            prediction = data['model'].predict(X_new)
            sentiment = data['label_encoder'].inverse_transform(prediction)[0]
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
        errors = []
        for mot in tokens:
            for e in verifier_phonotactique(mot):
                errors.append({
                    "mot": mot,
                    "regle": e.regle,
                    "description": e.description
                })
        return Response({
            "texte": texte,
            "errors": errors,
            "isValid": len(errors) == 0
        })

class LemmatizationAPIView(APIView):
    def post(self, request):
        texte = get_text_from_request(request)
        tokens = tokeniser(texte)
        result = {mot: lemmatiser(mot) for mot in tokens}
        return Response({'texte': texte, 'lemmes': result})