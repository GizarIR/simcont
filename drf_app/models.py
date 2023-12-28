import json
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from drf_app.validators import validate_json


from users.models import CustomUser


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
            'vocabularylemma__frequency'
        ).order_by('-vocabularylemma__frequency')

        order_lemmas_dict = {}

        for item in qs_lemmas:
            order_lemmas_dict[item['lemma']] = item['vocabularylemma__frequency']

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

    def __str__(self):
        return f"('{self.id}', '{self.learner}', '{self.vocabulary}')"


class Board(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)
    set_lemmas = models.JSONField(null=True, blank=True, validators=[validate_json], default=None)

    # TODO Need update func update_set_lemmas to according with algorithm
    def update_set_lemmas(self):
        """
            1) Проверяем EducationLemma на наличие New And On_Study, длину словаря
            2) Если все до limit_lemmas_item * limit_lemmas_period в  On_Study то Берем из Словаря следующие
            не выученные слова по порядку
            3) Иначе берем On_Study + New до limit_lemmas_item * limit_lemmas_period
        """
        set_result = {}
        list_lemmas = Education.get_list_lemmas_from_voc(self.education)
        for i in range(0, len(list_lemmas)-1):
            set_result[i] = list_lemmas[i]
        self.set_lemmas = json.dumps(set_result, ensure_ascii=False)


class Lemma(models.Model):
    class Pos(models.TextChoices):
        X = "X", _("other")
        ADJ = "ADJ", _("adjective")
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
        # TODO update when DB will clear (as the same StatusEducation )
        ROOKIE = "Rookie", _("Rookie")
        IN_PROGRESS = "In_Progress", _("In progress")
        TRANSLATED = "Translated", _("Translated")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lemma = models.CharField(max_length=150)
    pos = models.CharField(
        max_length=5,
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
        max_length=11,
        choices=TranslateStatus.choices,
        default=TranslateStatus.ROOKIE,
    )

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
