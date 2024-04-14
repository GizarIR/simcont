import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.dispatch import Signal

from simcont import settings
from .models import Vocabulary, Education, Board
from .tasks import create_order_lemmas_async, translate_lemma_async

logger = logging.getLogger(__name__)

translate_lemma_signal = Signal()


@receiver(translate_lemma_signal)
def translate_lemma_get(sender, **kwargs):
    lemma = kwargs['lemma']
    lang_to = kwargs['lang_to']
    # Task for Celery
    translate_lemma_async.apply_async(
        args=[lemma.pk, settings.DEFAULT_STRATEGY_TRANSLATE, lang_to],
        countdown=0
    )


@receiver(post_save, sender=Vocabulary)
def order_lemmas_create(sender, instance, created, **kwargs):
    if created:
        logger.info(f'Send source_txt to Celery for create order_lemmas for vocabulary: {instance.pk}')
        create_order_lemmas_async.apply_async(args=[instance.pk], countdown=1)
        instance.save()
    return None


@receiver(post_save, sender=Education)
def board_create(sender, instance, created, **kwargs):
    if created:
        logger.info(f'Create Board for Education: {instance.pk}')
        instance.save()
        board = Board.objects.create(education=instance)
        board.update_set_lemmas()
        board.save()

