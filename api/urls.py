# api/urls.py
from django.urls import path
from .views import AutocompleteView, TTSView

urlpatterns = [
    path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
    path('tts/', TTSView.as_view(), name='tts'),
]