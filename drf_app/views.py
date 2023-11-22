from django.shortcuts import render
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Vocabulary, Lemma, Lang
from .serializers import VocabularySerializer, LemmaSerializer


class CustomAutoSchema(SwaggerAutoSchema):
    """
    Overriding for group endpoints by ViewSets
    Add param <my_tag> to ViewSet
    """
    def get_tags(self, operation_keys=None):
        tags = self.overrides.get('tags', None) or getattr(self.view, 'my_tags', [])
        if not tags:
            tags = [operation_keys[0]]
        return tags


class VocabularyViewSet(viewsets.ModelViewSet):
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer

    my_tags = ['Vocabulary']

    # For describe custom queryset
    # More information https://proproprogs.ru/django/drf-simplerouter-i-defaultrouter
    # def get_queryset(self):
    #        pk = self.kwargs.get("pk")
    #
    #     if not pk:
    #         return Vocabulary.objects.all()[:3]
    #
    #     return Vocabulary.objects.filter(pk=pk)

    # Custom Route for Languages model
    # More information https://proproprogs.ru/django/drf-simplerouter-i-defaultrouter
    @action(methods=['get', 'post'], detail=False)
    def languages(self, request):
        """
        For end points /api/v1/vocabulary/languages/
        """
        langs = Lang.objects.all()
        return Response([
            {
                'id': lang.id,
                'name': lang.name,
                'short_name': lang.short_name
            } for lang in langs
        ])

    @action(methods=['get', 'put'], detail=True)
    def language(self, request, pk=None):
        """
        For endpoints /api/v1/vocabulary/{id}/language/
        """
        lang = Lang.objects.get(pk=pk)
        return Response({
            'id': lang.id,
            'name': lang.name,
            'short_name': lang.short_name
        })


class LemmaViewSet(viewsets.ModelViewSet):
    queryset = Lemma.objects.all()
    serializer_class = LemmaSerializer

    my_tags = ['Lemma']
