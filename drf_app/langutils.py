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

# https://github.com/xtekky/gpt4free?tab=readme-ov-file#-getting-started
import g4f

# https://spacy.io/usage
import spacy

# https://gtts.readthedocs.io/en/latest/index.html
# from gtts import gTTS

from tqdm import tqdm
import uuid
import logging

# Import by different ways depend on way of start file
if 'DJANGO_SETTINGS_MODULE' in os.environ:
    # if Django start
    from django.conf import settings
else:
    # else console start
    import logging.config
    from simcont import settings
    logging.config.dictConfig(settings.LOGGING)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)
# print(f"Level of logging set up on: {logger.getEffectiveLevel()}")

openai.api_key = settings.OPENAI_API_KEY


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
                logger.info(f"{lemma}: {frequency}")

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
    def clean_text(row_text: str, cons_mode: bool = False) -> str:
        if cons_mode:
            logger.info(f'Cleaning punctuation marks...')
        clearing_text = re.sub(r'[^\w\s]', '', row_text)
        if cons_mode:
            logger.info(f'Cleaning words with numbers...')
        clearing_text = re.sub(r'\b\d+\b', '', clearing_text)  # word only numbers
        clearing_text = re.sub(
            r'\b\w*\d\w*\b', lambda match: re.sub(r'\d', '', match.group()),
            clearing_text
        )  # words with numbers
        if cons_mode:
            logger.info(f'Cleaning words with a length of 1 character...')
        clearing_text = re.sub(r'\b\w{1}\b', '', clearing_text)
        clearing_text = clearing_text.replace('\n', ' ')
        clearing_text = ' '.join(clearing_text.split())  # Удаляем лишние пробелы
        return str(clearing_text)

    @staticmethod
    def create_order_lemmas(source_text: str, cons_mode: bool = False) -> dict:
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
        doc = SimVoc.nlp_instance(source_text.lower())
        unsorted_result = defaultdict(int)
        doc_len = len(doc)
        if cons_mode:
            progress_bar = tqdm(total=doc_len, desc="Found lemmas...", unit="token", unit_scale=1)
            for i in range(doc_len):
                lemma = doc[i].lemma_.strip()
                if lemma and "\\" not in lemma:
                    unsorted_result[doc[i].lemma_] += 1

                progress_bar.update(1)
                time.sleep(0.0001)

            progress_bar.close()
        else:
            for i in range(doc_len):
                lemma = doc[i].lemma_.strip()
                if lemma and "\\" not in lemma:
                    unsorted_result[doc[i].lemma_] += 1

        order_lemmas = dict(sorted(unsorted_result.items(), key=lambda item: item[1], reverse=True))

        return order_lemmas

    # TODO need add handle of Errors when strategy func get wrong data in response
    @staticmethod
    def strategy_get_translate_chatgpt(text_to_translate: str, lang_to: str,  num_extra_translate: int = 1) -> str:
        # TODO need to translate promt_to_ai to Eng for support different languages
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
                str(num_extra_translate),
                text_to_translate,
                text_to_translate,
            ),
            max_tokens=512,  # Max count of tokens in response
            temperature=0,
            n=1,
            stop=None,
            timeout=50  # Options: set timeout for request
        )
        logger.info(f"Number of tokens for request: {response['usage']['total_tokens']}")
        response = response.choices[0].text.strip()
        response_str = response.replace('\n', '')
        response_data = json.loads(response_str)
        response_data["user_inf"] = []
        return json.dumps(response_data, ensure_ascii=False)  # JSON string

    @staticmethod
    def strategy_get_translate_g4f(text_to_translate: str, lang_to: str, num_extra_translate: int = 1) -> str:
        # g4f.debug.logging = True  # Enable debug logging
        g4f.debug.version_check = False  # Disable automatic version checking
        # print(g4f.Provider.Bing.params)  # Print supported args for Bing
        prompt_to_ai = (
            "Переведи на {} слово {} с не больше {} дополнительных значений "
            "в формате:"
            "{{"
            "\"main_translate\": [ \"{}\", \"произношение\", \"перевод\", \"часть речи в UP Tags\"],"
            "\"extra_data\": [[ \"{}\", \"перевод\", \"часть речи\"], ...]"
            "}}"
        )

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[
                {"role": "user",
                 "content": prompt_to_ai.format(
                     LANGUAGES[lang_to],
                     text_to_translate,
                     str(num_extra_translate),
                     text_to_translate,
                     text_to_translate,
                     )
                 }
            ],
        )

        response = response.strip()
        response_str = response[response.find('main_translate')-2:response.find('}')+1]
        response_str = response_str.replace('\n', '')
        # logger.info(response_str)
        response_data = json.loads(response_str)
        response_data["user_inf"] = []
        return json.dumps(response_data, ensure_ascii=False)  # JSON string

    @staticmethod
    def strategy_get_translate_gtrans(text_to_translate: str, lang_to: str) -> str:
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
        SimVoc.load_spacy_model()

        # Process the sentence using the loaded model
        doc = SimVoc.nlp_instance(text_to_translate)

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

    @staticmethod
    def get_token(phrase: str) -> list:
        """
            Result of function contain list of tokens. Token is object with:
            :text - source text of token
            :pos_ - part of speech by Simvoc.pos_mapping
            :dep_ - dependency between token
            :lemma_ - base form of token
        """
        SimVoc.load_spacy_model()
        doc = SimVoc.nlp_instance(phrase)
        # print([(w.text, w.pos_ , w.lemma_, w.dep_) for w in doc])
        return [w for w in doc]


if __name__ == '__main__':

    # output_path = 'sandbox/output.txt'
    # source_path = 'sandbox/pmbok5en.pdf'
    # source_path = 'sandbox/test_article.pdf'
    # # source_path = 'sandbox/test_len_doc.pdf'
    # # source_path = 'sandbox/test_speech.txt'
    # current_path = os.path.abspath(__file__)
    # parent_path = os.path.dirname(os.path.dirname(current_path))  # up to 2 level
    # file_path = os.path.join(parent_path, source_path)
    # testVoc = SimVoc()
    # output_file_path = os.path.join(parent_path, output_path)
    #
    # with open(file_path, 'rb') as file:
    #     result = testVoc.convert_to_txt(file, cons_mode=True)
    #     result = testVoc.clean_text(result)
    #     order_dict = testVoc.create_order_lemmas(result, cons_mode=True)
    #     logger.info(f"Hello logger!!!")
    #     testVoc.print_order_lemmas_console(order_dict)
    #     # print(order_dict)
    #
    # with open(output_file_path, 'w', encoding='utf-8') as output_file:
    #     output_file.write(result)



    # print(f"{'*' * 15} Test ChatGPT {'*' * 15}") # !!!СТОИТ ДЕНЕГ
    # translated_dict = json.loads(SimVoc.strategy_get_translate_chatgpt('orange', 'ru')) # to JSON object
    # print(translated_dict)
    # { 'main_translate': ['orange', 'ˈɒrɪndʒ', 'апельсин', 'NOUN'],
    # 'extra_main': [['orange', 'оранжевый', 'прилагательное'], ['orange', 'оранжевый цвет', 'существительное']]}

    # print(f"{'*' * 15} Test GT {'*' * 15}")
    # translated_dict = json.loads(SimVoc.strategy_get_translate_gtrans("Hello", "ru"))  # to JSON object - dict
    # print(translated_dict)

    # print(f"{'*' * 15} Test G4F {'*' * 15}")
    # translated_dict = json.loads(SimVoc.strategy_get_translate_g4f("hello", "ru", 1))  # to JSON object - dict
    # print(translated_dict)

    sentence = "Apple is looking at buying U.K. startup for $1 billion"
    print(f"For token: {sentence} lemma is: {SimVoc.get_token(sentence)[0].lemma_}")
