import logging

from django.db.models import Q
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from simcont import settings
from .models import Vocabulary, Lemma, Lang, VocabularyLemma, Education, Board
from .serializers import VocabularySerializer, LemmaSerializer, TranslateLemmaSerializer, LanguageSerializer, \
    EducationSerializer, BoardSerializer
from .tasks import translate_lemma_async

logger = logging.getLogger(__name__)


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
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Vocabulary']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Response({"detail": "You need to authorization."}, status=status.HTTP_401_UNAUTHORIZED)

        pk = self.kwargs.get("pk")

        if pk:
            try:
                vocabulary = Vocabulary.objects.get(pk=pk)
                if user.is_staff or user in vocabulary.learners.all():
                    return Vocabulary.objects.filter(pk=pk)
                else:
                    return Vocabulary.objects.none()
            except Vocabulary.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_staff:
            return Vocabulary.objects.all()

        return Vocabulary.objects.filter(Q(learners=user) | Q(author=user))

    @action(methods=['get'], detail=False, serializer_class=LanguageSerializer)
    def languages(self, request):
        """
        For end points /api/v1/vocabulary/languages/
        """
        langs = Lang.objects.all()
        serializer = self.get_serializer(langs, many=True)

        return Response(serializer.data)

    @action(methods=['get'], detail=True, serializer_class=LanguageSerializer)
    def language(self, request, pk=None):
        """
        For endpoints /api/v1/vocabulary/{id}/language/
        """
        try:
            lang = Lang.objects.get(pk=pk)
        except Lang.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(lang)
        return Response(serializer.data)


class LemmaViewSet(viewsets.ModelViewSet):
    queryset = Lemma.objects.all()
    serializer_class = LemmaSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Lemma']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Response({"detail": "You need to authorization."}, status=status.HTTP_401_UNAUTHORIZED)

        pk = self.kwargs.get("pk")

        if pk:
            try:
                vocabularies_id = VocabularyLemma.objects.filter(throughLemma=pk).values('throughVocabulary')
                vocabularies = Vocabulary.objects.filter(
                    Q(id__in=vocabularies_id) & (Q(author=user) | Q(learners=user))
                ).distinct()
                if user.is_staff or vocabularies:
                    return Lemma.objects.filter(pk=pk)
                else:
                    return Lemma.objects.none()
            except Lemma.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        vocabularies = Vocabulary.objects.filter(Q(author=user) | Q(learners=user))
        lemmas_id = VocabularyLemma.objects.filter(throughVocabulary__in=vocabularies).values('throughLemma')
        qs_result = Lemma.objects.filter(id__in=lemmas_id)

        return qs_result

    @action(methods=['get'], detail=True, serializer_class=TranslateLemmaSerializer)
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'lang_to',
            openapi.IN_QUERY,
            description="Language code to translate to, default = ru",
            type=openapi.TYPE_STRING
        ),
    ])
    def translate(self, request, pk=None):
        """
        For endpoints /api/v1/lemma/{id}/translate/
        """
        try:
            lemma = Lemma.objects.get(pk=pk)
        except Lemma.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        lang_to = request.query_params.get('lang_to', 'ru')

        if lemma.translate_status == Lemma.TranslateStatus.ROOKIE:
            # Task for Celery
            translate_lemma_async.apply_async(
                args=[lemma.pk, settings.DEFAULT_STRATEGY_TRANSLATE, lang_to],
                countdown=0
            )
            logger.info(f"Start process of translate lemma: {lemma.lemma}, "
                        f"with strategy: {settings.DEFAULT_STRATEGY_TRANSLATE}")

        serializer = self.get_serializer(lemma)
        return Response(serializer.data)


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Education']


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Board']
