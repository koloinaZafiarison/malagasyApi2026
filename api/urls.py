# api/urls.py
from django.urls import path
from .views import AutocompleteView, SentimentAPIView

urlpatterns = [
    path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
     path('predict-sentiment/', SentimentAPIView.as_view(), name='predict-sentiment'),
]