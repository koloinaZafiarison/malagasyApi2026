# api/urls.py
from django.urls import path
from .views import AutocompleteView

urlpatterns = [
    path('autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
]