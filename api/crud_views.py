# api/crud_views.py
# CRUD complet pour les Documents via ModelViewSet

from rest_framework import serializers, viewsets, filters
from rest_framework.response import Response
from rest_framework import status

from .models import Document


# ── Serializer ───────────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Document
        fields = ["id", "title", "content", "word_count", "created_at", "updated_at"]
        read_only_fields = ["id", "word_count", "created_at", "updated_at"]


# ── ViewSet ──────────────────────────────────────────────

class DocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD complet sur les documents.

    GET    /api/crud/documents/          → liste (triée par updated_at desc)
    POST   /api/crud/documents/          → créer
    GET    /api/crud/documents/{id}/     → détail
    PATCH  /api/crud/documents/{id}/     → mise à jour partielle
    PUT    /api/crud/documents/{id}/     → mise à jour complète
    DELETE /api/crud/documents/{id}/     → supprimer

    Paramètres GET :
        ?search=mot   → filtre sur title et content
        ?ordering=title|-updated_at|created_at  → tri
    """

    queryset         = Document.objects.all()
    serializer_class = DocumentSerializer
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ["title", "content"]
    ordering_fields  = ["title", "created_at", "updated_at", "word_count"]
    ordering         = ["-updated_at"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
