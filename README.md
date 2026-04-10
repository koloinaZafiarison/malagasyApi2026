# Éditeur Teny Malagasy — Backend Django

API REST construite avec Django REST Framework pour l'éditeur de texte malagasy augmenté par l'IA.

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python create_empty_models.py   # Crée les .pkl de test
python manage.py runserver
```

## Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/api/health/` | Statut de l'API et des modèles |
| POST | `/api/spell-check/` | Correcteur orthographique |
| POST | `/api/autocomplete/` | Prédiction du mot suivant |
| POST | `/api/lemmatize/` | Racine d'un mot |
| POST | `/api/sentiment/` | Analyse de sentiment |
| POST | `/api/translate/` | Traduction mot-à-mot |
| POST | `/api/ner/` | Reconnaissance d'entités |
| POST | `/api/tts/` | Synthèse vocale |
| POST | `/api/chat/` | Chatbot assistant |

## Structure des modèles .pkl

```
ml_models/
├── spell_checker.pkl   → { dictionary: set() }
├── autocomplete.pkl    → { mot: { suivant: fréquence } }
├── lemmatizer.pkl      → { forme: { root, prefix, suffix } }
├── sentiment.pkl       → { positive_words: [], negative_words: [] }
├── translator.pkl      → { mot_mg: { fr: "...", en: "..." } }
└── ner.pkl             → { cities: [], persons: [], organizations: [] }
```

## Remplacer un modèle

Entraînez votre modèle, sérialisez-le avec `pickle.dump()` en respectant
la structure ci-dessus, puis déposez le fichier dans `ml_models/`.
Le serveur le chargera automatiquement au prochain démarrage.
