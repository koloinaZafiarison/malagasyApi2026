# api/urls.py
from django.urls import path
from .views import AutocompleteView, SentimentAPIView, OrthographeAPIView, PhonotactiqueAPIView, LemmatizationAPIView
urlpatterns = [
    path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
     path('predict-sentiment/', SentimentAPIView.as_view(), name='predict-sentiment'),

    path('orthographe/', OrthographeAPIView.as_view(), name='orthographe'),
    path('phonotactique/', PhonotactiqueAPIView.as_view(), name='phonotactique'),
    path('lemmatisation/', LemmatizationAPIView.as_view(), name='lemmatisation'),
]