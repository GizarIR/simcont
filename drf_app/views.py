from django.shortcuts import render

from rest_framework import generics
from .models import Vocabulary, Lemma
from .serializers import VocabularySerializer


class VocabularyAPIView(generics.ListCreateAPIView):
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer
