import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Vocabulary, Education, Board

from .tasks import create_order_lemmas_async

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Vocabulary)
def order_lemmas_create(sender, instance, created, **kwargs):
    logger.info(f'Send source_txt for START create order_lemmas for vocabulary: {instance.pk}')
    if created:
        # Send task to Celery
        create_order_lemmas_async.apply_async(args=[instance.pk], countdown=5)
        instance.save()
    return None


@receiver(post_save, sender=Education)
def board_create(sender, instance, created, **kwargs):
    logger.info(f'Create Board for Education: {instance.pk}')
    if created:
        instance.save()
        board = Board.objects.create(education=instance)
        board.update_set_lemmas()
        board.save()

