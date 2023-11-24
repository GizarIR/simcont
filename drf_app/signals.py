import json

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Vocabulary

from .tasks import create_order_lemmas_async


# TODO update func order_lemmas_created (add pk param)
@receiver(post_save, sender=Vocabulary)
def order_lemmas_create(sender, instance, created, **kwargs):
    print('Send source_txt fo r create order_lemmas for vocabulary:', instance)
    if created:
        # Выполните здесь ваш код для длительных вычислений
        result = create_order_lemmas_async.apply_async(args=[instance.source_text], countdown=5)
        # Сохраните результат в поле order_lemmas
        instance.save()
    return None
