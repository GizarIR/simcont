import uuid

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
from .models import Vocabulary, Lemma, Lang, VocabularyLemma, Education, Board, EducationLemma
from .serializers import VocabularySerializer, LemmaSerializer, TranslateLemmaSerializer, LanguageSerializer, \
    EducationSerializer, BoardSerializer, EducationLemmaSerializer, VocabularyLemmaSerializer
from .signals import translate_lemma_signal
# from .tasks import translate_lemma_async

from .langutils import SimVoc

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
        Get available languages.
        """
        langs = Lang.objects.all()
        serializer = self.get_serializer(langs, many=True)

        return Response(serializer.data)

    @action(methods=['get'], detail=True, serializer_class=LanguageSerializer)
    def language(self, request, pk=None):
        """
        Get language by id.
        """
        try:
            lang = Lang.objects.get(pk=pk)
        except Lang.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(lang)
        return Response(serializer.data)

    @action(methods=['post', 'patch'], detail=True, serializer_class=VocabularyLemmaSerializer)
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['id_lemma', 'frequency'],
            properties={
                'id_lemma': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Lemma's UUID for add to vocabulary"
                ),
                'frequency': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Frequency (weight) lemma in vocabulary",
                    default=0,
                ),
            },
        ),
        responses={
            200: VocabularyLemmaSerializer(),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def lemma(self, request, pk=None):
        """
        Add or update lemma in vocabulary.
        Params:
        *pk - vocabulary's UUID for add lemma
        *id_lemma - lemma's UUID which add to vocabulary
        *frequency - frequency (weight) lemma in vocabulary
        """
        try:
            vocabulary = Vocabulary.objects.get(pk=pk)
        except Vocabulary.DoesNotExist:
            return Response({"detail": "Not found vocabulary."}, status=status.HTTP_404_NOT_FOUND)

        id_lemma = request.data.get('id_lemma', None)

        try:
            lemma = Lemma.objects.get(pk=uuid.UUID(id_lemma))
        except Vocabulary.DoesNotExist:
            return Response({"detail": "Not found lemma."}, status=status.HTTP_404_NOT_FOUND)

        value = request.data.get('frequency', 0)

        if request.method == 'POST':
            if not VocabularyLemma.objects.filter(Q(throughLemma=lemma) & Q(throughVocabulary=vocabulary)).exists():
                lemma.vocabularies.add(vocabulary, through_defaults={"frequency": value})
                lemma.save()
                qs_lemma_for_voc = VocabularyLemma.objects.filter(
                    Q(throughLemma=lemma) & Q(throughVocabulary=vocabulary))
                lemma_voc = qs_lemma_for_voc[0]
            else:
                return Response({"detail": "Lemma for exactly Vocabulary exist, use method PATCH ."},
                                status=status.HTTP_400_BAD_REQUEST)

        else:  # elif request.method == 'PATCH':
            qs_lemma_for_voc = VocabularyLemma.objects.filter(
                Q(throughLemma=lemma) & Q(throughVocabulary=vocabulary))

            if not qs_lemma_for_voc:
                return Response({"detail": "Not found Lemma for exactly Vocabulary."},
                                status=status.HTTP_400_BAD_REQUEST)

            lemma_voc = qs_lemma_for_voc[0]
            lemma_voc.frequency = value
            lemma_voc.save()

        serializer = self.get_serializer(lemma_voc)
        return Response(serializer.data)


class LemmaViewSet(viewsets.ModelViewSet):
    queryset = Lemma.objects.all()
    serializer_class = LemmaSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Lemma']

    def create(self, request, *args, **kwargs):
        lemma_data = request.data
        existing_lemma = Lemma.objects.filter(lemma=lemma_data.get('lemma')).exists()

        if existing_lemma:
            return Response(
                {"detail": "This lemma already exists. Please use the existing ID instead of creating a new entry."},
                status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

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
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'lang_to',
                openapi.IN_QUERY,
                description="Language code to translate to, default = ru",
                type=openapi.TYPE_STRING),
        ],
        responses={
            200: TranslateLemmaSerializer(),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def translate(self, request, pk=None):
        """
        For translate lemma by id using strategy.
        Params:
        *lang_to - translate lemma to lang_to language
        """
        try:
            lemma = Lemma.objects.get(pk=pk)
        except Lemma.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        lang_to = request.query_params.get('lang_to', 'ru')

        if lemma.translate_status == Lemma.TranslateStatus.ROOKIE:
            translate_lemma_signal.send(sender=self.__class__, lemma=lemma, lang_to=lang_to)

            # Task for Celery
            # translate_lemma_async.apply_async(
            #     args=[lemma.pk, settings.DEFAULT_STRATEGY_TRANSLATE, lang_to],
            #     countdown=0
            # )

            logger.info(f"Start process of translate lemma: {lemma.lemma}, "
                        f"with strategy: {settings.DEFAULT_STRATEGY_TRANSLATE}")

        serializer = self.get_serializer(lemma)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="Token for check and get id lemma",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: LemmaSerializer(),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    @action(methods=['get'], detail=False, serializer_class=LemmaSerializer, pagination_class=None)
    def get_id_lemma_by_token(self, request):
        """
        For check a lemma and get id by token (string word).
        Params:
        *token - token for check
        """
        token = request.query_params.get('token', '')
        if not token:
            return Response({"detail": "Bad request."}, status=status.HTTP_400_BAD_REQUEST)

        checking_lemma = SimVoc.get_token(token)[0].lemma_
        try:
            lemma = Lemma.objects.get(lemma=checking_lemma)
        except Lemma.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(lemma)
        return Response(serializer.data)


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Education']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Response({"detail": "You need to authorization."}, status=status.HTTP_401_UNAUTHORIZED)

        pk = self.kwargs.get("pk")

        if pk:
            try:
                education = Education.objects.get(pk=pk)
                if user.is_staff or user == education.learner:
                    return Education.objects.filter(pk=pk)
                else:
                    return Education.objects.none()
            except Education.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_staff:
            return Education.objects.all()

        return Education.objects.filter(learner=user)


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    my_tags = ['Board']

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Response({"detail": "You need to authorization."}, status=status.HTTP_401_UNAUTHORIZED)

        pk = self.kwargs.get("pk")

        if pk:
            try:
                board = Board.objects.get(pk=pk)
                education = Education.objects.get(pk=board.education_id)
                if user.is_staff or user == education.learner:
                    return Board.objects.filter(pk=pk)
                else:
                    return Board.objects.none()
            except Board.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_staff:
            return Board.objects.all()

        return Board.objects.filter(education__in=Education.objects.filter(learner=user).values('id'))

    @action(methods=['get'], detail=True, serializer_class=BoardSerializer)
    def update_set_lemmas(self, request, pk=None):
        """
            Update set of lemmas for exactly board
        """
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        board.update_set_lemmas()

        serializer = self.get_serializer(board)
        return Response(serializer.data)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'id_lemma',
            openapi.IN_QUERY,
            description="UUID ID lemma",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ])
    @action(methods=['get'], detail=True, serializer_class=EducationLemmaSerializer)
    def get_study_status(self, request, pk=None):
        """
            Get lemma's study status for exactly education's board
        """
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        education = board.education

        id_lemma_value = request.query_params.get('id_lemma', '')

        if id_lemma_value is None:
            return Response({"detail": "'id_lemma' are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        qs_lemma_for_edu = EducationLemma.objects.filter(Q(throughLemma=id_lemma_value) & Q(throughEducation=education))

        if not qs_lemma_for_edu:
            return Response({"detail": "Not found Lemma for exactly Education."}, status=status.HTTP_400_BAD_REQUEST)

        lemma = qs_lemma_for_edu[0]

        serializer = self.get_serializer(lemma)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type='object',
            properties={
                'status': openapi.Schema(
                    type='string',
                    enum=['NE', 'ST', 'LE'],
                    description='The status value (choose one of the enum values NE - New, ST - On_Study, LE - Learned)'
                ),
                'id_lemma': openapi.Schema(
                    type='string',
                    description='The UUID ID_lemma value'
                ),
            },
            required=['status', 'id_lemma']
        ),
        responses={
            200: EducationLemmaSerializer(),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    @action(methods=['patch'], detail=True, serializer_class=EducationLemmaSerializer)
    def set_study_status(self, request, pk=None):
        """
            Update lemma's study status for exactly education's board
        """
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        education = board.education

        status_value = request.data.get('status')
        id_lemma_value = request.data.get('id_lemma')

        qs_lemma_for_edu = EducationLemma.objects.filter(Q(throughLemma=id_lemma_value) & Q(throughEducation=education))
        if not qs_lemma_for_edu:
            return Response({"detail": "Not found Lemma for exactly Education."}, status=status.HTTP_400_BAD_REQUEST)

        if status_value is None or id_lemma_value is None:
            return Response({"detail": "Both 'status' and 'id_lemma' are required in the request body."},
                            status=status.HTTP_400_BAD_REQUEST)

        if status_value not in [choice for choice in EducationLemma.StatusEducation]:
            return Response({"detail": "Invalid value for 'status'."}, status=status.HTTP_400_BAD_REQUEST)

        lemma = qs_lemma_for_edu[0]
        lemma.status = status_value
        lemma.save()

        serializer = self.get_serializer(lemma)
        return Response(serializer.data)
