# https://pypi.org/project/googletrans/
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any

import pdfplumber
from googletrans import Translator, LANGUAGES

# https://platform.openai.com/docs/quickstart?context=python
import openai

# https://spacy.io/usage
import spacy

# https://gtts.readthedocs.io/en/latest/index.html
# from gtts import gTTS

from tqdm import tqdm
import uuid
import logging

from simcont import settings

openai.api_key = settings.OPENAI_API_KEY
logger = logging.getLogger(__name__)


class PartSpeech(str, Enum):
    X = "X"  # other
    ADJ = "ADJ"  # adjective
    ADP = "ADP"  # adposition
    ADV = "ADV"  # adverb
    AUX = "AUX"  # auxiliary
    CCONJ = "CCONJ"  # coordinating conjunction
    DET = "DET"  # determiner
    INTJ = "INTJ"  # interjection
    NOUN = "NOUN"  # noun
    NUM = "NUM"  # numeral
    PART = "PART"  # particle
    PRON = "PRON"  # pronoun
    PROPN = "PROPN"  # proper noun
    PUNCT = "PUNCT"  # punctuation
    SCONJ = "SCONJ"  # subordinating conjunction
    SYM = "SYM"  # symbol
    SPACE = "SPACE"
    VERB = "VERB"  # verb


class SimVoc:
    """
    SimVoc - class which contain specifically functions for handle vocabulary for app SimCont
    """
    SPACY_MODEL = "en_core_web_sm"
    NLP_MAX_LENGTH = int(settings.NLP_MAX_LENGTH)
    nlp_instance = None

    pos_mapping = {
        "X": PartSpeech.X,
        "ADJ": PartSpeech.ADJ,
        "ADP": PartSpeech.ADP,
        "ADV": PartSpeech.ADV,
        "AUX": PartSpeech.AUX,
        "CCONJ": PartSpeech.CCONJ,
        "DET": PartSpeech.DET,
        "INTJ": PartSpeech.INTJ,
        "NOUN": PartSpeech.NOUN,
        "NUM": PartSpeech.NUM,
        "PART": PartSpeech.PART,
        "PRON": PartSpeech.PRON,
        "PROPN": PartSpeech.PROPN,
        "PUNCT": PartSpeech.PUNCT,
        "SCONJ": PartSpeech.SCONJ,
        "SPACE": PartSpeech.SPACE,
        "SYM": PartSpeech.SYM,
        "VERB": PartSpeech.VERB
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

    @classmethod
    def load_spacy_model(cls):
        if cls.nlp_instance is None:
            cls.nlp_instance = spacy.load(cls.SPACY_MODEL)
            cls.nlp_instance.max_length = cls.NLP_MAX_LENGTH

    @staticmethod
    def print_order_lemmas_console(lemmas_dict: dict, limit: int = 1) -> Any:
        for lemma, frequency in lemmas_dict.items():
            if frequency >= limit:
                print(f"{lemma}: {frequency}")

    @staticmethod
    def convert_to_txt(file_obj, cons_mode=False):
        """
        Support file's format:
            TXT, PDF
        """
        logger.info(f"Func convert_to_txt starts to read file {file_obj.name}.")
        doc_txt = ""
        _, file_extension = os.path.splitext(file_obj.name)
        if file_extension.lower() == '.pdf':
            with pdfplumber.open(file_obj) as pdf:
                if cons_mode:
                    progress_bar = tqdm(total=len(pdf.pages), desc="Read pages...", unit="page", unit_scale=1)
                    for page in pdf.pages:
                        doc_txt += page.extract_text()
                        progress_bar.update(1)
                    progress_bar.close()
                else:
                    for page in pdf.pages:
                        doc_txt += page.extract_text()
            return doc_txt
        elif file_extension.lower() == '.txt':
            return file_obj.read().decode('utf-8')
        else:
            return ""

    @staticmethod
    def clean_text(row_text: str) -> str:
        print(f'Cleaning punctuation marks...')
        clearing_text = re.sub(r'[^\w\s]', '', row_text)
        # print(f'Cleaning the newline characters...')
        # clearing_text = clearing_text.replace('\n', '')
        print(f'Cleaning words with numbers...')
        clearing_text = re.sub(r'\w*\d\w*', '', clearing_text)
        print(f'Cleaning words with a length of 1 character...')
        clearing_text = re.sub(r'\b\w{1}\b', '', clearing_text)
        return str(clearing_text)

    @staticmethod
    def create_order_lemmas(source_text: str, types: list[str] = None, cons_mode: bool = False) -> dict:
        """
        Order like this:
        json {
            'lemma1': 12,
            'lemma2': 11
              }
        """
        # Load the 'en_core_web_sm' model
        SimVoc.load_spacy_model()

        # Process the sentence using the loaded model
        # doc = nlp(source_text)
        doc = SimVoc.nlp_instance(source_text)
        unsorted_result = defaultdict(int)
        doc_len = len(doc)
        if cons_mode:
            progress_bar = tqdm(total=doc_len, desc="Found lemmas...", unit="token", unit_scale=1)
            for i in range(doc_len):

                if not types or doc[i].pos_ in types:
                    lemma = doc[i].lemma_.strip()
                    if lemma and "\\" not in lemma:
                        unsorted_result[doc[i].lemma_.lower()] += 1

                    progress_bar.update(1)
                    time.sleep(0.0001)
            progress_bar.close()
        else:
            for i in range(doc_len):

                if not types or doc[i].pos_ in types:
                    lemma = doc[i].lemma_.strip()
                    if lemma and "\\" not in lemma:
                        unsorted_result[doc[i].lemma_.lower()] += 1

        order_lemmas = dict(sorted(unsorted_result.items(), key=lambda item: item[1], reverse=True))

        return order_lemmas

    @staticmethod
    def get_translate_chatgpt(text_to_translate: str, lang_to: str,  num: int = 1) -> str:
        prompt_to_ai = (
            "Переведи на {} слово {} с не больше {} дополнительных значений "
            "в формате:"
            "{{"
            "\"main_translate\": [ {}, произношение, перевод, часть речи в UP Tags],"
            "\"extra_data\": [[ {}, перевод, часть речи], ...]"
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
        response_data["user_inf"] = []
        return json.dumps(response_data, ensure_ascii=False)  # JSON string

    @staticmethod
    def get_translate_gtrans(text_to_translate: str, lang_to: str) -> str:
        """
            For work well you need specific version googletrans==4.0.0-rc1
            Translate text_to_translate using FREE googletrans service
            :param text_to_translate:  word which you need to translate
            :type text_to_translate: string
            :param lang_to: language which you want to get translate
            :type lang_to: string, limit 2 symbols, for example - 'ru', 'en', 'de'
        """
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
                SimVoc.pos_mapping.get(pos_tags[0][1], 'X'),
            ],
            "extra_data": [],
            "users_inf": []
        }
        return json.dumps(response_data, ensure_ascii=False)  # to JSON string


if __name__ == '__main__':
    # source_path = 'sandbox/pmbok5en.pdf'
    source_path = 'sandbox/test_article.pdf'
    # source_path = 'sandbox/test_len_doc.pdf'
    # source_path = 'sandbox/test_speech.txt'
    current_path = os.path.abspath(__file__)
    parent_path = os.path.dirname(os.path.dirname(current_path))  # up to 2 level
    file_path = os.path.join(parent_path, source_path)
    testVoc = SimVoc()

    with open(file_path, 'rb') as file:
        result = testVoc.convert_to_txt(file, cons_mode=True)
        result = testVoc.clean_text(result)
        order_dict = testVoc.create_order_lemmas(result, cons_mode=True)
        testVoc.print_order_lemmas_console(order_dict)
        # print(order_dict)


    # print(f"{'*' * 15} Test ChatGPT {'*' * 15}") # !!!СТОИТ ДЕНЕГ
    # translated_dict = json.loads(SimVoc.get_translate_chatgpt('orange', 'ru')) # to JSON object
    # print(translated_dict)
    # { 'main_translate': ['orange', 'ˈɒrɪndʒ', 'апельсин', 'существительное'],
    # 'extra_main': [['orange', 'оранжевый', 'прилагательное'], ['orange', 'оранжевый цвет', 'существительное']]}

    # print(f"{'*' * 15} Test GT {'*' * 15}")
    # translated_dict = json.loads(SimVoc.get_translate_gtrans("people", "ru"))  # to JSON object - dict
    # print(translated_dict)
