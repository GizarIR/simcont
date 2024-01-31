import base64
import json
import os
import time
import unittest
import uuid


import fitz

from unittest.mock import patch

from django.db.models.signals import post_save
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from drf_app.langutils import SimVoc
from rest_framework.test import APIClient, APITestCase

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from drf_app.models import Lang, Vocabulary, Lemma
from drf_app.signals import order_lemmas_create
from drf_app.tasks import create_order_lemmas_async
from users.models import CustomUser
from django.contrib.auth import get_user_model

import logging
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


class LangUtilsTestCase(unittest.TestCase):
    def setUp(self):
        # For test_print_order_lemmas_console
        self.lemmas_dict = {'lemma1': 5, 'lemma2': 4, 'lemma3': 1}

        # For test_convert_to_txt_txt_file
        current_file_path = os.path.abspath(__file__)
        project_directory = os.path.dirname(current_file_path)
        txt_file_path = os.path.join(project_directory, 'test_file.txt')
        with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write("Test content for txt file.")

        pdf_file_path = os.path.join(project_directory, 'test_file.pdf')
        pdf_document = fitz.open()
        pdf_page = pdf_document.new_page()
        pdf_page.insert_text((100, 100), "Test content for pdf file.")
        pdf_document.save(pdf_file_path)
        pdf_document.close()

        # For test_strategy_get_translate_gtrans
        self.client = APIClient()

    def tearDown(self):
        # For test_convert_to_txt_txt_file
        project_directory = os.path.dirname(os.path.abspath(__file__))
        txt_file_path = os.path.join(project_directory, 'test_file.txt')
        pdf_file_path = os.path.join(project_directory, 'test_file.pdf')
        os.remove(txt_file_path)
        os.remove(pdf_file_path)

    @patch('drf_app.langutils.logger.info')
    def test_print_order_lemmas_console(self, mock_logger_info):
        logger.info(f"test_print_order_lemmas_console")
        instance = SimVoc()
        instance.print_order_lemmas_console(self.lemmas_dict, limit=2)
        expected_calls = [unittest.mock.call('lemma1: 5'), unittest.mock.call('lemma2: 4')]
        mock_logger_info.assert_has_calls(expected_calls)

    @staticmethod
    def built_test_path_file(file_name: str) -> str:
        current_file_path = os.path.abspath(__file__)
        project_directory = os.path.dirname(current_file_path)
        return os.path.join(project_directory, file_name)

    @patch('drf_app.langutils.logger.info')
    def test_convert_to_txt_txt_file(self, mock_logger_info):
        logger.info(f"test_convert_to_txt_txt_file")
        instance = SimVoc()
        txt_file_path = self.built_test_path_file('test_file.txt')

        with open(txt_file_path, 'rb') as txt_file:
            result = instance.convert_to_txt(txt_file)

        expected_result = "Test content for txt file."
        self.assertEqual(result, expected_result)

        mock_logger_info.assert_called_once_with(f"Func convert_to_txt starts to read file {txt_file_path}.")

    @patch('drf_app.langutils.logger.info')
    def test_convert_to_txt_pdf_file(self, mock_logger_info):
        logger.info(f"test_convert_to_txt_pdf_file")
        instance = SimVoc()
        pdf_file_path = self.built_test_path_file('test_file.pdf')

        with open(pdf_file_path, 'rb') as pdf_file:
            result = instance.convert_to_txt(pdf_file)

        expected_result = "Test content for pdf file."
        self.assertEqual(result, expected_result)

        mock_logger_info.assert_called_once_with(f"Func convert_to_txt starts to read file {pdf_file_path}.")

    def test_clean_text(self):
        logger.info(f"test_clean_text")
        input_text = "Hello, 123 world!\nThis is a test1."
        cons_mode = False

        expected_output = "Hello world This is test"
        cleaned_text = SimVoc.clean_text(input_text, cons_mode)

        self.assertEqual(cleaned_text, expected_output)

    def test_create_order_lemmas(self):
        logger.info(f"test_create_order_lemmas")
        source_text = "This is a sample nice sentence This comes another sentences"
        types = ["NOUN", "VERB", "ADJ"]
        cons_mode = False

        result = SimVoc.create_order_lemmas(source_text, types, cons_mode)
        expected_result = {'sentence': 2, 'sample': 1, 'nice': 1, 'come': 1}

        self.assertEqual(result, expected_result)

    def test_strategy_get_translate_gtrans(self):
        logger.info(f"test_strategy_get_translate_gtrans")
        text_to_translate = "hello"
        lang_to = "ru"

        result = SimVoc.strategy_get_translate_gtrans(text_to_translate, lang_to)
        expected_result = {
            'main_translate': ['hello', 'həˈlō', 'привет', 'INTJ'],
            'extra_data': [],
            'users_inf': []
        }

        self.assertEqual(json.loads(result), expected_result)

    def test_strategy_get_translate_g4f(self):
        """
        expected_result = {
            'main_translate': ['hello', '/hɛˈləʊ/', 'привет', 'INTJ'],
            'extra_data': [['hello', 'алло', 'INTJ']],
            'user_inf': []
        }
        """
        if settings.DEFAULT_STRATEGY_TRANSLATE != "get_translate_g4f":
            logger.info(f"Test test_strategy_get_translate_g4f missed")
        else:
            logger.info(f"test_strategy_get_translate_g4f")

            text_to_translate = "hello"
            lang_to = "ru"
            num_extra_translate = 1

            result = SimVoc.strategy_get_translate_g4f(text_to_translate, lang_to, num_extra_translate)
            result_dict = json.loads(result)
            self.assertIsInstance(result, str)
            self.assertIn("main_translate", result)
            self.assertIn("extra_data", result)
            self.assertIn("user_inf", result)
            self.assertNotEquals(result_dict["main_translate"], [])
            self.assertNotEquals(result_dict["extra_data"], [])

    def test_strategy_get_translate_chatgpt(self):
        if settings.DEFAULT_STRATEGY_TRANSLATE != "get_translate_chatgpt":
            logger.info(f"Test test_strategy_get_translate_chatgpt missed")
        else:
            logger.info(f"test_strategy_get_translate_chatgpt")
            text_to_translate = "hello"
            lang_to = "ru"
            num_extra_translate = 1

            result = SimVoc.strategy_get_translate_chatgpt(text_to_translate, lang_to, num_extra_translate)
            result_dict = json.loads(result)
            self.assertIsInstance(result, str)
            self.assertIn("main_translate", result)
            self.assertIn("extra_data", result)
            self.assertIn("user_inf", result)
            self.assertNotEquals(result_dict["main_translate"], [])
            self.assertNotEquals(result_dict["extra_data"], [])


# TODO create test for endpoints

class VocabularyTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_data = {
            "email": "test@example.com",
            "password": "testpassword",
        }

        # Create common data
        cls.lang_from = Lang.objects.create(name='English', short_name='en')
        cls.lang_to = Lang.objects.create(name='Russian', short_name='ru')
        # TODO create signal for CustomUser model - post_save and
        #  use:
        #  post_save.disconnect(send_activation_email, sender=CustomUser)
        #  ...
        #  post_save.connect(send_activation_email, sender=CustomUser)
        user = CustomUser.objects.create_user(**user_data)
        user.is_active = True
        user.activation_code = None
        user.save()
        cls.user = user

        cls.vocabulary_data = {
            'title': 'Test Vocabulary',
            'description': 'Test Description',
            'lang_from': str(cls.lang_from.id),
            'lang_to': str(cls.lang_to.id),
            'source_text': 'Test Source Text Test',
            'author': str(cls.user.id),
            'learners_id': [str(cls.user.id)],
        }

        access_token = AccessToken.for_user(cls.user)
        cls.access_token = str(access_token)
        cls.client = APIClient()
        cls.client.credentials(HTTP_AUTHORIZATION=f'Bearer {cls.access_token}')

        # Create instance of Vocabulary for tests
        post_save.disconnect(order_lemmas_create, sender=Vocabulary)  # without fill order_lemmas field

        url = reverse('vocabulary-list')
        response = cls.client.post(url, cls.vocabulary_data, format='json')
        cls.created_vocabulary = Vocabulary.objects.get(pk=response.json()['id'])

        post_save.connect(order_lemmas_create, sender=Vocabulary)

    def setUp(self):
        # Check auth
        profile_response = VocabularyTests.client.get('/users/profile/', format='json')
        if profile_response.status_code != status.HTTP_200_OK:
            logger.info(f"Login failed. Test response content: {profile_response.content}")

    def test_create_vocabulary(self):
        logger.info(f"test_create_vocabulary")
        # order_lemmas_create(sender=Vocabulary, instance=self.created_vocabulary, created=True)
        create_order_lemmas_async(self.created_vocabulary.id)
        self.assertEqual(Vocabulary.objects.count(), 1)
        self.assertIsNotNone(Vocabulary.objects.get(pk=self.created_vocabulary.id).order_lemmas)
        self.assertEqual(Lemma.objects.count(), 3)
        self.assertEqual(self.created_vocabulary.title, 'Test Vocabulary')

    def test_retrieve_vocabulary(self):
        logger.info(f"test_retrieve_vocabulary")
        url = reverse('vocabulary-detail', args=[str(self.created_vocabulary.id)])
        response = VocabularyTests.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Vocabulary')


if __name__ == '__main__':
    unittest.main()
