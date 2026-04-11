from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.translator import translate_word

@api_view(["GET"])
def translate_view(request):
    word = request.GET.get("word")

    if not word:
        return Response({"error": "Veuillez fournir un mot"}, status=400)

    result = translate_word(word)

    return Response(result)