from django.shortcuts import render

from rest_framework import generics, viewsets
from .models import Vocabulary, Lemma
from .serializers import VocabularySerializer


class VocabularyViewSet(viewsets.ModelViewSet):
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer
