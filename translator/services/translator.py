import pandas as pd
import os
from django.conf import settings
import requests
from bs4 import BeautifulSoup
import urllib3

CSV_PATH = os.path.join(settings.BASE_DIR, "translator", "data", "dictionnaire.csv")
df = pd.read_csv(CSV_PATH)

# dictionnaire rapide
dict_fr = {
    row["Francais"]: {
        "mg": row["Malagasy"],
        "en": row["Anglais"]
    }
    for _, row in df.iterrows()
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

    soup = BeautifulSoup(response.text, "html.parser")

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

#Fonction qui orchestre la traduction
def translate_word(word):
    word = word.lower().strip()

    # LOCAL : matching avec le dataset local
    if word in dict_fr:
        return {
            "mg": dict_fr[word]["mg"],
            "en": dict_fr[word]["en"],
            "source": "local"
        }

    #Fallback si les données locales ne sont pas suffisantes
    en = translate_word_to_english_fallback(word, "fr", "en")
    mg = get_mg_result(word)

    return {
        "mg": mg if mg else "introuvable",
        "en": en if en else "not found"
    }