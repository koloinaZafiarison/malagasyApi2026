from rest_framework import serializers

class AutocompleteRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, allow_blank=False)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)

class SuggestionSerializer(serializers.Serializer):
    word = serializers.CharField()
    prob = serializers.FloatField()