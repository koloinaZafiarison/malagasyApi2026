# api/views.py
import json
import pickle
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Charger une seule fois au démarrage
with open("vectorisation_TF_IDF.pkl", "rb") as f:
    vectorizer = pickle.load(f)

with open("random_forest_model.pkl", "rb") as f:
    model = pickle.load(f)

def predire_message_texte(message: str):
    X = vectorizer.transform([message])
    y_pred = model.predict(X)[0]
    prediction = str(y_pred)  # "ham" ou "spam"
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        class_index = list(model.classes_).index(y_pred)
        confidence = float(proba[class_index] * 100)
        return {"label": prediction, "confidence": confidence}
    else:
        # fallback si le modèle ne fournit pas predict_proba
        return {"label": prediction, "confidence": None}

@csrf_exempt
def predict_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    message = data.get("message", "")

    label = predire_message_texte(message)
    return JsonResponse({"prediction": label})