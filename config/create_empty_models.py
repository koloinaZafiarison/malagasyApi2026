"""
create_empty_models.py
----------------------
Crée des fichiers .pkl vides avec la bonne structure
pour tester l'API sans les vrais modèles entraînés.

Usage :
    python create_empty_models.py

Les vrais .pkl (entraînés sur corpus malagasy) doivent
respecter exactement ces structures pour être compatibles
avec les views.
"""

import pickle
from pathlib import Path

MODELS_DIR = Path(__file__).parent / 'ml_models'
MODELS_DIR.mkdir(exist_ok=True)


models = {

    # ── Correcteur orthographique ─────────────────────────
    # dictionary : set de mots malagasy valides
    'spell_checker.pkl': {
        'dictionary': {
            'ny', 'sy', 'fa', 'aho', 'ianao', 'izy', 'isika', 'izany',
            'manao', 'maka', 'mandeha', 'trano', 'lamba', 'vary', 'rano',
            'tokony', 'tena', 'tsara', 'ratsy', 'lehibe', 'kely',
            'Antananarivo', 'Toamasina', 'Mahajanga', 'Fianarantsoa',
            'malagasy', 'gasy', 'vazaha',
        }
    },

    # ── Autocomplétion N-gram ─────────────────────────────
    # Format : { mot_contexte: { mot_suivant: fréquence } }
    'autocomplete.pkl': {
        'ny':      {'trano': 15, 'lamba': 8,  'rano': 6,   'vary': 5},
        'manao':   {'inona': 10, 'ahoana': 7, 'izany': 5},
        'tsara':   {'ny': 12,   'tokoa': 8,  'izany': 6},
        'aho':     {'dia': 9,   'tsy': 7,    'te': 5,     'manao': 4},
        'isika':   {'rehetra': 8, 'dia': 6,  'tokony': 5},
        'tokony':  {'hanao': 7, 'hianatra': 5, 'hiasa': 4},
    },

    # ── Lemmatiseur ──────────────────────────────────────
    # Format : { forme_fléchie: { root, prefix, suffix } }
    'lemmatizer.pkl': {
        'manosika':  {'root': 'tosika',  'prefix': 'man',  'suffix': ''},
        'mandeha':   {'root': 'deha',    'prefix': 'man',  'suffix': ''},
        'manasa':    {'root': 'sasa',    'prefix': 'man',  'suffix': ''},
        'mihinana':  {'root': 'hinana',  'prefix': 'mi',   'suffix': ''},
        'mianatra':  {'root': 'ianatra', 'prefix': 'mi',   'suffix': ''},
        'ianarana':  {'root': 'ianatra', 'prefix': '',     'suffix': 'ana'},
        'fanaovana': {'root': 'ao',      'prefix': 'fan',  'suffix': 'ana'},
        'fisaorana': {'root': 'saora',   'prefix': 'fi',   'suffix': 'ana'},
    },

    # ── Analyse de sentiment ─────────────────────────────
    # Format : { positive_words: [...], negative_words: [...] }
    'sentiment.pkl': {
        'positive_words': [
            'tsara', 'soa', 'faly', 'mahafaly', 'midera', 'sitraka',
            'fiadanana', 'fahafaham-po', 'tia', 'mahafinaritra',
            'voahasina', 'hendry', 'nahomby', 'lasa', 'faneva',
        ],
        'negative_words': [
            'ratsy', 'tsy', 'mafy', 'marary', 'olana', 'ory',
            'fadiranovana', 'sahirana', 'kivy', 'tahotra',
            'malahelo', 'mahantra', 'loza', 'diso', 'hadino',
        ],
    },

    # ── Dictionnaire de traduction ───────────────────────
    # Format : { mot_mg: { fr: "...", en: "..." } }
    'translator.pkl': {
        'trano':    {'fr': 'maison',     'en': 'house'},
        'rano':     {'fr': 'eau',        'en': 'water'},
        'vary':     {'fr': 'riz',        'en': 'rice'},
        'lamba':    {'fr': 'tissu',      'en': 'cloth'},
        'tsara':    {'fr': 'bien/beau',  'en': 'good/nice'},
        'ratsy':    {'fr': 'mauvais',    'en': 'bad'},
        'lehibe':   {'fr': 'grand',      'en': 'big'},
        'kely':     {'fr': 'petit',      'en': 'small'},
        'mandeha':  {'fr': 'partir/aller', 'en': 'go'},
        'tia':      {'fr': 'aimer',      'en': 'love'},
        'rano':     {'fr': 'eau',        'en': 'water'},
        'malagasy': {'fr': 'malgache',   'en': 'malagasy'},
        'gasy':     {'fr': 'malgache',   'en': 'malagasy'},
        'aho':      {'fr': 'je/moi',     'en': 'I/me'},
        'ianao':    {'fr': 'tu/toi',     'en': 'you'},
        'izy':      {'fr': 'il/elle',    'en': 'he/she'},
    },

    # ── NER — Entités nommées ────────────────────────────
    # Format : { cities: [...], persons: [...], organizations: [...] }
    'ner.pkl': {
        'cities': [
            'Antananarivo', 'Toamasina', 'Mahajanga', 'Fianarantsoa',
            'Toliara', 'Antsiranana', 'Antsirabe', 'Ambositra',
            'Morondava', 'Ambanja', 'Nosy Be', 'Manakara',
            'Farafangana', 'Mananara', 'Sambava', 'Andapa',
        ],
        'persons': [
            'Andrianampoinimerina', 'Ranavalona', 'Radama',
            'Rainilaiarivony', 'Andry Rajoelina', 'Marc Ravalomanana',
            'Didier Ratsiraka',
        ],
        'organizations': [
            'HVM', 'TIM', 'AREMA', 'ENAM', 'HJRA',
            'Université d\'Antananarivo', 'ISP Madagascar',
            'Air Madagascar', 'Telma', 'Orange Madagascar',
        ],
    },
}


def create_models():
    for filename, data in models.items():
        path = MODELS_DIR / filename
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✓ Créé : {path}")

    print(f"\n✅ {len(models)} modèles créés dans {MODELS_DIR}/")
    print("\nStructure des modèles :")
    for filename, data in models.items():
        keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        print(f"  {filename:30s} → clés : {keys}")


if __name__ == '__main__':
    create_models()
