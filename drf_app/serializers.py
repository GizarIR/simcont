from rest_framework import serializers
from .models import Vocabulary, Lemma, Lang


class VocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = ('title', 'description', 'time_create', 'time_update', 'is_active',
                  'lang_from', 'lang_to', 'order_lemmas', 'source_text', 'users')
