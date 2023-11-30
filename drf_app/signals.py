from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Vocabulary

from .tasks import create_order_lemmas_async


@receiver(post_save, sender=Vocabulary)
def order_lemmas_create(sender, instance, created, **kwargs):
    print('Send source_txt for START create order_lemmas for vocabulary:', instance.pk)
    if created:
        # Send task to Celery
        create_order_lemmas_async.apply_async(args=[instance.pk], countdown=5)
        instance.save()
    return None