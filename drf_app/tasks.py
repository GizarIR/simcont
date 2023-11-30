import json

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist


from .langutils import SimVoc
from .models import Vocabulary, Lemma


# TODO update func create_order_lemmas_async using logging
@shared_task
def create_order_lemmas_async(voc_id) -> None:
    try:
        vocabulary = Vocabulary.objects.get(pk=voc_id)
        if not vocabulary:
            print(f"Vocabulary with id {voc_id} does not exist.")
            return None

        with transaction.atomic():
            order_lemmas_dict = SimVoc.create_order_lemmas(vocabulary.source_text)
            order_lemmas_json = json.dumps(order_lemmas_dict, ensure_ascii=False)
            vocabulary.order_lemmas = order_lemmas_json
            vocabulary.save()

            for key, value in order_lemmas_dict.items():
                if not Lemma.objects.filter(lemma=key).exists():
                    new_lemma = Lemma.objects.create(lemma=key, pos=value[1])
                    new_lemma.vocabularies.add(vocabulary, through_defaults={"frequency": value[0]})
                    # new_lemma.save()
                else:
                    cur_lemma = Lemma.objects.filter(lemma=key)[0]
                    cur_lemma.vocabularies.add(vocabulary, through_defaults={"frequency": value[0]})
                    # cur_lemma.save()

            print(f"Finished process of create order_lemmas for {voc_id}")

    except ObjectDoesNotExist:
        print(f"Vocabulary with id {voc_id} does not exist.")
    except ValueError as e:
        print(f"Error converting {voc_id} to UUID: {e}")
    except SoftTimeLimitExceeded:
        print("Task time limit exceeded.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
