from django.urls import path
from .views import translate_view

urlpatterns = [
    path("translate/", translate_view),
]