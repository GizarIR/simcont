from django.shortcuts import render

from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Vocabulary, Lemma, Lang
from .serializers import VocabularySerializer


class VocabularyViewSet(viewsets.ModelViewSet):
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer

    # For describe custom queryset
    # def get_queryset(self):
    #     pass

    # Custom Route for Languages model
    @action(methods=['get', 'post'], detail=False)
    def languages(self, request):
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
        lang = Lang.objects.get(pk=pk)
        return Response({
            'id': lang.id,
            'name': lang.name,
            'short_name': lang.short_name
        })
