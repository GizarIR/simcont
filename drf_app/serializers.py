from drf_yasg import openapi
from rest_framework import serializers
from .models import Vocabulary, Lemma, Lang, Education, Board

from users.serializers import LearnerSerializer
from users.models import CustomUser


class OrderLemmasField(serializers.JSONField):
    """
    Example:
    {
        "lemma_1": 100,
        "lemma_2": 58,
        ...
        "lemma_N": 1,
    }
    """
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Order of lemmas for vocabulary",
            "additional_properties": openapi.Schema(
                title="Words and their frequency",
                type=openapi.TYPE_INTEGER,  # Assuming frequency is represented by integers
                default=None,
            ),
        }


class VocabularySerializer(serializers.ModelSerializer):
    order_lemmas = OrderLemmasField(required=False, allow_null=True)
    learners = LearnerSerializer(many=True, read_only=True)
    learners_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=True,
        many=True
    )

    class Meta:
        model = Vocabulary
        fields = ('id', 'title', 'description', 'time_create', 'time_update', 'is_active',
                  'lang_from', 'lang_to', 'order_lemmas', 'source_text', 'author', 'learners',
                  'learners_id', 'order_lemmas_updated')

    def create(self, validated_data):
        learners = validated_data.pop('learners_id', None)
        vocabulary = Vocabulary.objects.create(**validated_data)
        for learner in learners:
            vocabulary.learners.add(learner.id)
        vocabulary.save()
        return vocabulary


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


class TranslateLemmaSerializer(serializers.ModelSerializer):
    translate = TranslateField()

    class Meta:
        model = Lemma
        fields = ('id', 'lemma',  'pos', 'translate', 'translate_status')


class LanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lang
        fields = ('id', 'name', 'short_name')


# TODO Serializators for Education, Board

class EducationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Education
        fields = ('id', 'learner', 'vocabulary', 'time_create', 'time_update', 'is_finished')


class BoardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Board
        fields = ('id', 'education', 'limit_lemmas_item', 'limit_lemmas_period', 'set_lemmas')


class LemmaSerializer(serializers.ModelSerializer):
    # For definition type of JSON field in Swagger use link:
    # https://drf-yasg.readthedocs.io/en/stable/custom_spec.html#:~:text=class%20EmailMessageField(,%3D%20EmailMessageField()
    vocabularies = VocabularySerializer(many=True, read_only=True)
    vocabularies_id = serializers.PrimaryKeyRelatedField(
        queryset=Vocabulary.objects.all(),
        write_only=True,
        many=True
    )
    educations = EducationSerializer(many=True, read_only=True)
    educations_id = serializers.PrimaryKeyRelatedField(
        queryset=Education.objects.all(),
        write_only=True,
        many=True
    )

    translate = TranslateField()

    class Meta:
        model = Lemma
        fields = (
            'id', 'lemma', 'pos', 'translate',
            'vocabularies', 'vocabularies_id',
            'educations', 'educations_id',
            'translate_status'
        )

    def create(self, validated_data):
        vocabularies = validated_data.pop('vocabularies_id', None)
        educations = validated_data.pop('educations_id', None)
        lemma = Lemma.objects.create(**validated_data)
        for voc in vocabularies:
            lemma.vocabularies.add(voc.id)
        for edu in educations:
            lemma.educations.add(edu.id)
        lemma.save()
        return lemma
