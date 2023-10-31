import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import CustomUser


class Vocabulary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=300, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    lang_from = models.CharField(max_length=2)
    lang_to = models.CharField(max_length=2)
    order_lemmas = models.JSONField()
    source_text = models.TextField()
    users = models.ForeignKey("users.CustomUser", on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.title


class Lemma(models.Model):
    class Pos(models.TextChoices):
        NOUN = "NOUN", _("Noun")
        ADJ = "ADJ", _("Adjective")
        VERB = "VERB", _("Verb")
        PROPN = "PROPN", _("Preposition")
        PRON = "PRON", _("Pronoun")
        CONJ = "CONJ", _("Conjunction")
        PART = "PART", _("Particle")
        INTERJ = "INTERJ", _("Interjection")
        UNKNOWN = "UNKNOWN", _("Unknown")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # TODO Continue here
    pos = models.CharField(
        max_length=7,
        choices=Pos.choices,
        default=Pos.UNKNOWN,
    )


class VocabularyLemma(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Pos(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


