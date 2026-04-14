# api/urls.py
from django.urls import path
from django.http import HttpResponse
# from .views import (
#     AutocompleteView,
#     SentimentAPIView,
#     OrthographeAPIView,
#     PhonotactiqueAPIView,
#     LemmatizationAPIView,
#     TTSView,
# )
def home(request):
    return HttpResponse("API is running")

urlpatterns = [
    path('', home),
    # path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
    # path('predict-sentiment/', SentimentAPIView.as_view(), name='predict-sentiment'),
    # path('orthographe/', OrthographeAPIView.as_view(), name='orthographe'),
    # path('phonotactique/', PhonotactiqueAPIView.as_view(), name='phonotactique'),
    # path('lemmatisation/', LemmatizationAPIView.as_view(), name='lemmatisation'),
    # path('tts/', TTSView.as_view(), name='tts'),
]