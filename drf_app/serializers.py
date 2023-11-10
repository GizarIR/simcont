from rest_framework import serializers
from .models import Vocabulary, Lemma, Lang, VocabularyLemma


class VocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = ('id', 'title', 'description', 'time_create', 'time_update', 'is_active',
                  'lang_from', 'lang_to', 'order_lemmas', 'source_text', 'users')


class LemmaSerializer(serializers.ModelSerializer):
    # For definition type of JSON field in Swagger use link:
    # https://drf-yasg.readthedocs.io/en/stable/custom_spec.html#:~:text=class%20EmailMessageField(,%3D%20EmailMessageField()
    vocabularies = VocabularySerializer(many=True, read_only=True)
    vocabularies_id = serializers.PrimaryKeyRelatedField(
        queryset=Vocabulary.objects.all(),
        write_only=True,
        many=True
    )

    class Meta:
        model = Lemma
        fields = ('id', 'lemma',  'pos', 'translate', 'vocabularies', 'vocabularies_id')

    def create(self, validated_data):
        vocabularies = validated_data.pop('vocabularies_id', None)
        lemma = Lemma.objects.create(**validated_data)
        for voc in vocabularies:
            lemma.vocabularies.add(voc.id)
        lemma.save()
        return lemma
