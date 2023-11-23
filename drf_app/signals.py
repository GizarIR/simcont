from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Vocabulary

from .tasks import create_order_lemmas_async

# TODO update func order_lemmas_created
@receiver(post_save, sender=Vocabulary)
def order_lemmas_created(instance, **kwargs):
    print('START update order_lemmas for vocabulary:', instance)
    create_order_lemmas_async.delay() # or apply_async()

