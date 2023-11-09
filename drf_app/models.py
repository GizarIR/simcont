import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from drf_app.validators import validate_json
# from users.models import CustomUser


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
    order_lemmas = models.JSONField(null=True, blank=True, validators=[validate_json])
    source_text = models.TextField()
    users = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.title


class Lemma(models.Model):
    class Pos(models.TextChoices):
        UNKNOWN = "UNKNOWN", _("Unknown")
        NOUN = "NOUN", _("Noun")
        ADJ = "ADJ", _("Adjective")
        VERB = "VERB", _("Verb")
        PROPN = "PROPN", _("Preposition")
        PRON = "PRON", _("Pronoun")
        CONJ = "CONJ", _("Conjunction")
        PART = "PART", _("Particle")
        INTERJ = "INTERJ", _("Interjection")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lemma = models.CharField(max_length=150)
    pos = models.CharField(
        max_length=7,
        choices=Pos.choices,
        default=Pos.UNKNOWN,
    )
    translate = models.JSONField(blank=True)
    vocabularies = models.ManyToManyField(
        Vocabulary,
        through="VocabularyLemma",
    )

    def __str__(self):
        return self.lemma


class VocabularyLemma(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    lemma = models.ForeignKey(Lemma, on_delete=models.CASCADE)
    frequency = models.IntegerField(default=0)

    def __str__(self):
        return f"('{self.vocabulary}', '{self.lemma}', '{self.frequency}')"
