import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser

from .tasks import send_activation_email_async

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def send_activation_email(sender, instance, created, **kwargs):
    logger.info(f'Send data to Celery for send activation email: {instance.email}')
    if created:
        # Send task to Celery
        send_activation_email_async.delay(instance.id)
        instance.save()
    return None
