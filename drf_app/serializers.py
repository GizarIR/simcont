from drf_yasg import openapi
from rest_framework import serializers
from .models import Vocabulary, Lemma, Lang, VocabularyLemma


class OrderLemmasField(serializers.JSONField):
    """
    Example:
    {
        "lemma_1": ["100"],
        "lemma_2": ["58"],
        ...
        "lemma_N": ["1"],
    }
    """
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Order of lemmas for vocabulary",
            "additional_properties": openapi.Schema(
                title="Words and their frequency and other params if you need",
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
            ),
        }


class VocabularySerializer(serializers.ModelSerializer):
    order_lemmas = OrderLemmasField()

    class Meta:
        model = Vocabulary
        fields = ('id', 'title', 'description', 'time_create', 'time_update', 'is_active',
                  'lang_from', 'lang_to', 'order_lemmas', 'source_text', 'users')


class TranslateField(serializers.JSONField):
    """
    Example:
    {
        "main_translate": ["orange", "ˈɒrɪndʒ", "апельсин", "существительное"],
        "extra_main": [["orange", "оранжевый", "прилагательное"], ["orange", "оранжевый цвет", "существительное"]],
        "users_inf": [{"user_id_1": "какой то специфичный перевод от пользователя"}, ...]
    }
    """

    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Translation",
            "properties": {
                "main_translate": openapi.Schema(
                    title="Main translate of lemma",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                ),
                "extra_main": openapi.Schema(
                    title="Extra translations of lemma",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                    ),
                ),
                "users_inf": openapi.Schema(
                    title="User extra information or translate \"user_id\": \"translate\"",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        additional_properties=openapi.Schema(type=openapi.TYPE_STRING),
                    ),
                ),
            },
            "required": ["main_translate", "extra_main", "users_inf"],
        }


class LemmaSerializer(serializers.ModelSerializer):
    # For definition type of JSON field in Swagger use link:
    # https://drf-yasg.readthedocs.io/en/stable/custom_spec.html#:~:text=class%20EmailMessageField(,%3D%20EmailMessageField()
    vocabularies = VocabularySerializer(many=True, read_only=True)
    vocabularies_id = serializers.PrimaryKeyRelatedField(
        queryset=Vocabulary.objects.all(),
        write_only=True,
        many=True
    )
    translate = TranslateField()

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
