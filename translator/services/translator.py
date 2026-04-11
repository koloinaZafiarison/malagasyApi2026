import pandas as pd
import os
from django.conf import settings
import requests
from bs4 import BeautifulSoup
import urllib3
from difflib import get_close_matches

CSV_PATH = os.path.join(settings.BASE_DIR, "translator", "data", "dictionnaire.csv")
df = pd.read_csv(CSV_PATH)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def normalize(text):
    return str(text).lower().strip()

#Normalisation du dataset
def explode_dataset(df):
    rows = []

    for _, row in df.iterrows():
        fr = row["Francais"]
        mg_list = str(row["Malagasy"]).split(",")
        en = row["Anglais"]

        for mg in mg_list:
            rows.append({
                "Francais": normalize(fr),
                "Malagasy": normalize(mg),
                "Anglais": normalize(en)
            })

    return pd.DataFrame(rows)

df = explode_dataset(df)

df["fr_norm"] = df["Francais"]
df["mg_norm"] = df["Malagasy"]
df["en_norm"] = df["Anglais"]


def search_exact(word, df):
    word = normalize(word)

    return df[
        (df["fr_norm"] == word) |
        (df["mg_norm"] == word) |
        (df["en_norm"] == word)
    ]

#recherche sur les voisins 
def search_fuzzy(word, df, threshold=0.8):
    word = normalize(word)

    all_words = (
        df["Francais"].tolist() +
        df["Malagasy"].tolist() +
        df["Anglais"].tolist()
    )

    all_words_norm = [normalize(w) for w in all_words]

    matches = get_close_matches(word, all_words_norm, n=5, cutoff=threshold)

    if not matches:
        return pd.DataFrame()

    mask = (
        df["Francais"].str.lower().isin(matches) |
        df["Malagasy"].str.lower().isin(matches) |
        df["Anglais"].str.lower().isin(matches)
    )

    return df[mask]


#Fonction qui appelle l'API pour traduire en anglais (fallback)
def translate_word_to_english_fallback(word, source="fr", target="en"):
    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": word,
        "langpair": f"{source}|{target}"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        return data["responseData"]["translatedText"]

    except Exception as e:
        print("API error:", e)
        return None

#Fonction qui appelle l'api et Scraping des résultas venant de l'appel à l'api de teny malagasy
def translate_teny_malagasy(word):
    url = "https://www.tenymalagasy.org/bins/teny2"

    payload = {"w": word}

    response = requests.post(
        url,
        data=payload,
        verify=False,
        timeout=10
    )

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "lxml")

    results = []

    # CIBLER UNIQUEMENT td.main
    main_cells = soup.select("td.main")

    for cell in main_cells:
        row = cell.find_parent("tr")
        if not row:
            continue

        cols = row.find_all("td")

        cleaned_row = []

        for col in cols:
            # récupérer uniquement les liens dans le td
            links = col.find_all("a")

            if links:
                text = ", ".join(
                    a.get_text(strip=True)
                    for a in links
                    if a.get_text(strip=True)
                )
            else:
                text = col.get_text(strip=True)

            # ignorer texte vide
            if text and text.strip():
                cleaned_row.append(text)

        # garder seulement lignes valides
        if len(cleaned_row) >= 2:
            results.append(cleaned_row)

    return results

#Fonction sui regroupe les résultats en utilisant l'api de teny malagasy
def get_mg_result(word):
    result = translate_teny_malagasy(word)

    if not result:
        return None

    words = [item[0] for item in result if item and len(item) > 0]

    # enlever doublons
    words = list(set(words))

    return ", ".join(words) if words else None

def translate_word(word):
    raw_input = word              # 👈 garder le mot original
    word = normalize(word)

    # 1. exact match
    exact = search_exact(word, df)
    if not exact.empty:
        row = exact.iloc[0]

        return {
            "input": raw_input,
            "matched_field": "exact",
            "fr": row["Francais"],
            "mg": row["Malagasy"],
            "en": row["Anglais"],
            "source": "Dictionnaire locale"
        }

    # 2. fuzzy match
    fuzzy = search_fuzzy(word, df)
    if not fuzzy.empty:
        row = fuzzy.iloc[0]

        return {
            "input": raw_input,
            "matched_field": "fuzzy",
            "fr": row["Francais"],
            "mg": row["Malagasy"],
            "en": row["Anglais"],
            "source": "Recherche par voisin (fuzzy match)"
        }

    # 3. fallback
    en = translate_word_to_english_fallback(word, "fr", "en")
    mg = get_mg_result(word)

    return {
        "input": raw_input,
        "matched_field": "fallback",
        "fr": raw_input,
        "mg": mg if mg else "introuvable",
        "en": en if en else "introuvable",
        "source": "Appel API"
    }