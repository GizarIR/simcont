from celery import shared_task
from django.core.mail import send_mail
from .models import CustomUser
from simcont import settings


@shared_task
def send_activation_email(user_id):
    user = CustomUser.objects.get(pk=user_id)
    activation_code = user.activation_code if user.activation_code else CustomUser.generate_activation_code()

    user.activation_code = activation_code
    user.save()

    subject = f'Account activation'
    message = f'Your activation code: {activation_code}'
    from_email = settings.EMAIL_FROM
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)
