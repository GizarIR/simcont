# https://pypi.org/project/googletrans/
import json
import re
import time
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from googletrans import Translator, LANGUAGES

# https://platform.openai.com/docs/quickstart?context=python
import openai

# https://spacy.io/usage
import spacy

# https://gtts.readthedocs.io/en/latest/index.html
from gtts import gTTS

from simcont import settings
from tqdm import tqdm
import uuid


class PartSpeech(str, Enum):
    UNKNOWN = "UNKNOWN"
    NOUN = "NOUN"
    ADJ = "ADJ"
    VERB = "VERB"
    PROPN = "PROPN"
    PRON = "PRON"
    CONJ = "CONJ"
    PART = "PART"
    INTERJ = "INTERJ"


class SimVoc:
    """
    SimVoc - class which contain specifically functions for handle vocabulary for app SimCont
    """
    pos_mapping = {
        "UNKNOWN": PartSpeech.UNKNOWN,
        "NOUN": PartSpeech.NOUN,
        "ADJ": PartSpeech.ADJ,
        "VERB": PartSpeech.VERB,
        "PROPN": PartSpeech.PROPN,
        "PRON": PartSpeech.PRON,
        "CONJ": PartSpeech.CONJ,
        "PART": PartSpeech.PART,
        "INTERJ": PartSpeech.INTERJ,
    }

    def __init__(
            self,
            id_voc: uuid.UUID = None,
            title: str = "",
            description: str = "",
            time_create: datetime = datetime.min,
            time_update: datetime = datetime.min,
            is_active: bool = False,
            lang_from_id: uuid.UUID = uuid.UUID('00000000-0000-0000-0000-000000000000'),
            lang_to_id: uuid.UUID = uuid.UUID('00000000-0000-0000-0000-000000000000'),
            order_lemmas=None,
            source_text: str = "",
            users=None
    ):
        self.id = uuid.uuid4() if not id_voc else id_voc
        self.title = title
        self.description = description
        self.order_lemmas = order_lemmas
        self.time_create = time_create
        self.time_update = time_update
        self.is_active = is_active
        self.lang_from_id = lang_from_id
        self.lang_to_id = lang_to_id
        self.order_lemmas = order_lemmas if order_lemmas is not None else {}
        self.source_text = source_text
        self.users = users if users is not None else []

    @staticmethod
    def clean_text(row_text: str) -> str:
        print(f'Cleaning punctuation marks...')
        clearing_text = re.sub(r'[^\w\s]', '', row_text)
        print(f'Cleaning the newline characters...')
        clearing_text = clearing_text.replace('\n', '')
        print(f'Cleaning words with numbers...')
        clearing_text = re.sub(r'\w*\d\w*', '', clearing_text)
        print(f'Cleaning words with a length of 1 character...')
        clearing_text = re.sub(r'\b\w{1}\b', '', clearing_text)
        return clearing_text

    @staticmethod
    def create_order_lemmas(source_text: str) -> dict:
        # Load the 'en_core_web_sm' model
        nlp = spacy.load("en_core_web_sm")
        nlp.max_length = settings.NLP_MAX_LENGTH
        # Process the sentence using the loaded model
        doc = nlp(source_text)
        unsorted_result = {}
        doc_len = len(doc) - 1
        progress_bar = tqdm(total=doc_len, desc="Found lemmas...", unit="token", unit_scale=100)

        for i in range(doc_len):
            if doc[i].lemma_ in unsorted_result:
                unsorted_result[doc[i].lemma_] += 1
            else:
                unsorted_result[doc[i].lemma_] = 1
            progress_bar.update(1)
            time.sleep(0.0001)

        order_lemmas = dict(sorted(unsorted_result.items(), key=lambda item: item[1]['frequency'], reverse=True))

        return order_lemmas

    @staticmethod
    def get_translate_chatgpt(text_to_translate: str, lang_to: str,  num: int = 1) -> str:
        prompt_to_ai = (
            "Переведи на {} слово {} с не больше {} дополнительных значений "
            "в формате:"
            "{{"
            "\"main_translate\": [ {}, произношение, перевод, часть речи],"
            "\"extra_main\": [[ {}, перевод, часть речи], ...]"
            "}}"
        )

        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt_to_ai.format(
                LANGUAGES[lang_to],
                text_to_translate,
                str(num),
                text_to_translate,
                text_to_translate,
            ),
            max_tokens=512,  # Максимальное количество токенов в каждом запросе
            temperature=0,
            n=1,
            stop=None,
            timeout=50  # Опционально: установите таймаут на запрос
        )
        print(f"Number of tokens for request: {response['usage']['total_tokens']}")
        response = response.choices[0].text.strip()
        response_str = response.replace('\n', '')
        response_data = json.loads(response_str)
        return json.dumps(response_data, ensure_ascii=False)  # JSON string

    @staticmethod
    def get_translate_gtrans(text_to_translate: str, lang_to: str) -> str:
        translator = Translator()
        translated = translator.translate(text_to_translate, dest=lang_to)

        # Handle text by spaCy for POS
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text_to_translate)

        # Get POS
        pos_tags = [(token.text, token.pos_) for token in doc]

        response_data = {
            "main_translate": [
                translated.origin,
                translated.extra_data['origin_pronunciation'],
                translated.text,
                SimVoc.pos_mapping.get(pos_tags[0][1], 'UNKNOWN'),
            ],
            "extra_data": []
        }
        return json.dumps(response_data, ensure_ascii=False)  # to JSON string


if __name__ == '__main__':
    # source_path = 'source/pmbok5en.pdf'
    source_path = 'source/test_article.pdf'

