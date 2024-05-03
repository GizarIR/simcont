import json
import uuid

from rest_framework.exceptions import ValidationError as DRFValidationError
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from drf_app.validators import validate_json

import logging
logger = logging.getLogger(__name__)


class Lang(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=2)

    def __str__(self):
        return f"('{self.name}', '{self.short_name}')"


class Vocabulary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=300, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    lang_from = models.ForeignKey(Lang, related_name='voc_from', on_delete=models.CASCADE)
    lang_to = models.ForeignKey(Lang, related_name='voc_to', on_delete=models.CASCADE)
    order_lemmas = models.JSONField(null=True, blank=True, validators=[validate_json], default=None)
    source_text = models.TextField()
    author = models.ForeignKey("users.CustomUser", related_name='voc_author', on_delete=models.CASCADE, default=None)
    learners = models.ManyToManyField(
        "users.CustomUser",
        related_name='voc_learner',
        through="LearnerVocabulary",
    )

    @property
    def order_lemmas_updated(self):
        qs_lemmas = Lemma.objects.filter(
            vocabularies=self
        ).values(
            'lemma',
            'vocabularylemma__frequency',
            'id'
        ).order_by('-vocabularylemma__frequency')

        order_lemmas_dict = {}

        for item in qs_lemmas:
            order_lemmas_dict[item['lemma']] = [item['vocabularylemma__frequency'], str(item['id'])]

        order_lemmas_json = json.dumps(order_lemmas_dict, ensure_ascii=False)

        return order_lemmas_json

    def __str__(self):
        return f"({self.title}: {self.id})"


class LearnerVocabulary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    throughLearner = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    throughVocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)

    def __str__(self):
        return f"('{self.id}', '{self.throughLearner}', '{self.throughVocabulary}')"


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learner = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, default=None)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    limit_lemmas_item = models.PositiveIntegerField(default=2)
    limit_lemmas_period = models.PositiveIntegerField(default=7)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_finished = models.BooleanField(default=False)

    @staticmethod
    def get_list_lemmas_from_voc(education) -> list:
        order_lemmas = json.loads(Vocabulary.objects.get(pk=education.vocabulary.pk).order_lemmas_updated)
        return list(order_lemmas.keys())

    @staticmethod
    def get_list_id_lemmas_from_voc(education) -> list:
        order_lemmas = json.loads(Vocabulary.objects.get(pk=education.vocabulary.pk).order_lemmas_updated)
        return [item[1] for item in list(order_lemmas.values())]

    def __str__(self):
        return f"('{self.id}', '{self.learner}', '{self.vocabulary}')"


class Board(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    set_lemmas = models.JSONField(null=True, blank=True, validators=[validate_json], default=None)

    def get_set_lemmas_dict(self, next_lemmas: list = None) -> dict:
        """
            Get new set_lemmas dictionary for education.
            Params:
            *next_lemmas: list lemma's id which need to add in board
        """
        result = {}
        education = get_object_or_404(Education, pk=self.education.pk)
        if next_lemmas:
            for lemma in next_lemmas:
                EducationLemma.objects.create(
                    throughEducation=education,
                    throughLemma=Lemma.objects.get(pk=lemma),
                    status=EducationLemma.StatusEducation.NEW
                )

        list_edu_ns_upd = list(EducationLemma.objects.filter(
            Q(throughEducation=education.pk) &
            (Q(status=EducationLemma.StatusEducation.NEW) | Q(status=EducationLemma.StatusEducation.ON_STUDY))
        ).values_list('throughLemma', flat=True))

        # logger.info(f"Information for test: {[Lemma.objects.get(pk=lemma_id) for lemma_id in list_edu_ns_upd]}")

        for day in range(1, education.limit_lemmas_period + 1):
            result[day] = [
                str(list_edu_ns_upd.pop(0)) if len(list_edu_ns_upd) else None for _ in range(education.limit_lemmas_item)
            ]

        return result

    def update_set_lemmas(self):
        """
           Update set_lemmas field in Board model
        """
        set_result = {}
        next_lemmas = []
        education_instance = get_object_or_404(Education, pk=self.education.pk)
        limits = education_instance.limit_lemmas_item * education_instance.limit_lemmas_period
        list_voc = Education.get_list_id_lemmas_from_voc(education_instance)

        if not len(list_voc):
            return None

        qs_lemmas_education = EducationLemma.objects.filter(
            throughEducation=education_instance.pk
        ).values_list('throughLemma', flat=True)
        list_edu_nsl = [str(item) for item in qs_lemmas_education]

        qs_lemmas_on_study = EducationLemma.objects.filter(
            Q(throughEducation=education_instance.pk) &
            (Q(status=EducationLemma.StatusEducation.NEW) | Q(status=EducationLemma.StatusEducation.ON_STUDY))
        ).values_list('throughLemma', flat=True)
        list_edu_ns = [str(item) for item in qs_lemmas_on_study]

        if len(list_edu_ns) >= limits:
            set_result = self.get_set_lemmas_dict()
        elif len(list_voc) > len(list_edu_nsl):
            need_lemmas = limits - len(list_edu_ns)
            # for all versions python
            next_lemmas = [item for item in list_voc if item not in list_edu_nsl][:need_lemmas]

            # only for more than python3.7 work faster (keep order items in list)
            # next_lemmas = list(set(list_voc)-set(list_edu_nsl))[:need_lemmas]
            set_result = self.get_set_lemmas_dict(next_lemmas)
        else:
            set_result = self.get_set_lemmas_dict()

        self.set_lemmas = json.dumps(set_result, ensure_ascii=False)

        # next_lemmas.clear()
        # list_voc.clear()
        # list_edu_nsl.clear()
        # list_edu_ns.clear()
        # set_result.clear()

        return None


class Lemma(models.Model):
    class Pos(models.TextChoices):
        X = "X", _("other")
        ADJ = "ADJ", _("adjective")
        ADJ_SAT = "ADJ_SAT", _("adjective satellite")
        ADP = "ADP", _("adposition")
        ADV = "ADV", _("adverb")
        AUX = "AUX", _("auxiliary")
        CCONJ = "CCONJ", _("coordinating conjunction")
        DET = "DET", _("determiner")
        INTJ = "INTJ", _("interjection")
        NOUN = "NOUN", _("noun")
        NUM = "NUM", _("numeral")
        PART = "PART", _("particle")
        PRON = "PRON", _("pronoun")
        PROPN = "PROPN", _("proper noun")
        PUNCT = "PUNCT", _("punctuation")
        SCONJ = "SCONJ", _("subordinating conjunction")
        SYM = "SYM", _("symbol")
        SPACE = "SPACE", _("space")
        VERB = "VERB", _("verb")

    class TranslateStatus(models.TextChoices):
        ROOKIE = "ROO", _("Rookie")
        IN_PROGRESS = "PRO", _("In progress")
        TRANSLATED = "TRA", _("Translated")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lemma = models.CharField(max_length=150)
    pos = models.CharField(
        max_length=7,
        choices=Pos.choices,
        default=Pos.X,
    )
    translate = models.JSONField(null=True, blank=True, validators=[validate_json], default=None)
    vocabularies = models.ManyToManyField(
        Vocabulary,
        through="VocabularyLemma",
    )
    educations = models.ManyToManyField(
        Education,
        through="EducationLemma",
    )
    translate_status = models.CharField(
        max_length=3,
        choices=TranslateStatus.choices,
        default=TranslateStatus.ROOKIE,
    )

    translate_source = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        existing_lemma = Lemma.objects.filter(lemma=self.lemma).exists()
        if not self.pk:  # only create (not update)
            if existing_lemma:
                raise DRFValidationError("This lemma already exists. "
                                         "Please use the existing ID instead of creating a new entry.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.lemma


class VocabularyLemma(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    throughVocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    throughLemma = models.ForeignKey(Lemma, on_delete=models.CASCADE)
    frequency = models.IntegerField(default=0)

    def __str__(self):
        return f"('{self.throughVocabulary}', '{self.throughLemma}', '{self.frequency}')"


class EducationLemma(models.Model):
    """
    This model contain data about only lemmas which added to Board for study
    """
    class StatusEducation(models.TextChoices):
        """
            New - added in Set,
            On_Study - learned in Set,
            Learned - learned in Board
        """
        NEW = "NE", _("New")
        ON_STUDY = "ST", _("On study")
        LEARNED = "LE", _("Learned")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    throughEducation = models.ForeignKey(Education, on_delete=models.CASCADE)
    throughLemma = models.ForeignKey(Lemma, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=2,
        choices=StatusEducation.choices,
        default=StatusEducation.NEW,
    )

    def __str__(self):
        return f"('{self.throughEducation}', '{self.throughLemma}', '{self.status}')"
