import json
import uuid
from typing import Any

from celery import shared_task

from .langutils import SimVoc
from .models import Vocabulary


# TODO update func create_order_lemmas_async
@shared_task
def create_order_lemmas_async(text_for_order) -> Any:
    # print(f"Started process of create order_lemmas for {vocabulary}")
    order_lemmas_created = json.dumps(SimVoc.create_order_lemmas(text_for_order), ensure_ascii=False)
    print(f"Finished process of create order_lemmas for {order_lemmas_created}")
    return None
