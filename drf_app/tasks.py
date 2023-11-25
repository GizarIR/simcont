import json
from uuid import UUID
from typing import Any

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .langutils import SimVoc
from .models import Vocabulary


# TODO update func create_order_lemmas_async
@shared_task
def create_order_lemmas_async(voc_id) -> None:
    try:
        vocabulary = Vocabulary.objects.get(pk=voc_id)

        if not vocabulary:
            print(f"Vocabulary with id {voc_id} does not exist.")
            return None

        with transaction.atomic():
            order_lemmas_created = json.dumps(SimVoc.create_order_lemmas(vocabulary.source_text), ensure_ascii=False)
            vocabulary.order_lemmas = order_lemmas_created
            vocabulary.save()

            print(f"Finished process of create order_lemmas for {order_lemmas_created}")
    except ObjectDoesNotExist:
        print(f"Vocabulary with id {voc_id} does not exist.")
    except ValueError as e:
        print(f"Error converting {voc_id} to UUID: {e}")
    except SoftTimeLimitExceeded:
        print("Task time limit exceeded.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
