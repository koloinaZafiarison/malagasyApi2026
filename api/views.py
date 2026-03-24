from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import re
import pickle
from typing import List, Dict, Any
from django.conf import settings
from dataclasses import dataclass
from .serializers import AutocompleteRequestSerializer, SentimentSerializer

# ----------------------------
# Chargement des modèles
# ----------------------------
MODEL_PATH = os.path.join(settings.BASE_DIR, 'models/autocomplete/malagasy_trigram.pkl')
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

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

class AutocompleteView(APIView):
    def predict_next(self, text: str, top_k: int = 5):
        if not hasattr(model, "autocomplete"):
            raise RuntimeError("Le modèle ne supporte pas l'autocomplétion.")
        return model.autocomplete(text, top_k)

    def post(self, request):
        data = request.data
        text = data.get('text', '')
        top_k = data.get('top_k', 5)
        suggestions = self.predict_next(text, top_k)
        result = [{'word': w, 'prob': p} for w, p in suggestions]
        return Response({'suggestions': result})

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
            text = serializer.validated_data['text']
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