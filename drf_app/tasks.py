import json
import logging
from typing import Callable

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist


from .langutils import SimVoc
from .models import Vocabulary, Lemma


logger = logging.getLogger(__name__)


@shared_task
def create_order_lemmas_async(voc_id) -> None:
    try:
        vocabulary = Vocabulary.objects.get(pk=voc_id)
        if not vocabulary:
            logger.info(f"Vocabulary with id {voc_id} does not exist.")
            return None

        with transaction.atomic():
            order_lemmas_dict = SimVoc.create_order_lemmas(vocabulary.source_text)
            order_lemmas_json = json.dumps(order_lemmas_dict, ensure_ascii=False)
            vocabulary.order_lemmas = order_lemmas_json
            vocabulary.save()

            for key, value in order_lemmas_dict.items():
                if not Lemma.objects.filter(lemma=key).exists():
                    new_lemma = Lemma.objects.create(lemma=key)
                    new_lemma.vocabularies.add(vocabulary, through_defaults={"frequency": value})
                    # new_lemma.save()
                else:
                    cur_lemma = Lemma.objects.filter(lemma=key)[0]
                    cur_lemma.vocabularies.add(vocabulary, through_defaults={"frequency": value})
                    # cur_lemma.save()

            logger.info(f"Finished process of create order_lemmas for {voc_id}")

    except ObjectDoesNotExist:
        logger.error(f"Vocabulary with id {voc_id} does not exist.")
    except ValueError as e:
        logger.error(f"Error converting {voc_id} to UUID: {e}")
    except SoftTimeLimitExceeded:
        logger.error("Task time limit exceeded.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None


@shared_task
def translate_lemma_async(lemma_id, strategy, lang_to) -> None:
    try:
        lemma = Lemma.objects.get(pk=lemma_id)
        if not lemma:
            logger.info(f"Lemma with id {lemma_id} does not exist.")
            return None

        with transaction.atomic():

            strategy_function: Callable = getattr(SimVoc, f"strategy_{strategy}", None)

            if strategy_function is not None and callable(strategy_function):
                lemma.translate_status = Lemma.TranslateStatus.IN_PROGRESS
                lemma.save()

                lemma_translated = strategy_function(lemma.lemma, lang_to)
                lemma.translate = lemma_translated

                _pos = json.loads(lemma_translated).get("main_translate", None)[3]
                lemma.pos = _pos or lemma.pos

                lemma.translate_status = Lemma.TranslateStatus.TRANSLATED

                lemma.save()
            logger.info(f"Finished process of get translate for lemma: {lemma.lemma}, "
                        f"with strategy: {strategy}")

    except ObjectDoesNotExist:
        logger.error(f"Lemma with id {lemma_id} does not exist.")
    except ValueError as e:
        logger.error(f"Error converting {lemma_id} to UUID: {e}")
    except SoftTimeLimitExceeded:
        logger.error("Task time limit exceeded.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None
