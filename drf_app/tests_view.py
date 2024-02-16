import os
import unittest

from django.db.models.signals import post_save
from django.urls import reverse
from rest_framework import status

from drf_app.models import Lang, Vocabulary, Lemma
from drf_app.signals import order_lemmas_create
from drf_app.tasks import create_order_lemmas_async

import logging

from users.tests import BaseUserCase

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


class BaseViewTestCase(BaseUserCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create common data
        try:
            cls.lang_from = Lang.objects.create(name='English', short_name='en')
            cls.lang_to = Lang.objects.create(name='Russian', short_name='ru')
        except Exception as e:
            logger.info(f"An error has occurred: {e}")

        cls.vocabulary_data = {
            'title': 'Test Vocabulary',
            'description': 'Test Description',
            'lang_from': str(cls.lang_from.id) if cls.lang_from else 'en',
            'lang_to': str(cls.lang_to.id) if cls.lang_from else 'ru',
            'source_text': 'Test Source Text Test',
            'author': str(cls.user.id),
            'learners_id': [str(cls.user.id)],
        }
        # Create instance of Vocabulary for tests
        post_save.disconnect(order_lemmas_create, sender=Vocabulary)  # without fill order_lemmas field

        url = reverse('vocabulary-list')
        response = cls.authenticated_client.post(url, cls.vocabulary_data, format='json')
        cls.created_vocabulary = Vocabulary.objects.get(pk=response.json()['id'])

        post_save.connect(order_lemmas_create, sender=Vocabulary)

        create_order_lemmas_async(Vocabulary.objects.first().id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up any data as needed
        cls.lang_from.delete()
        cls.lang_to.delete()
        cls.created_vocabulary.delete()


class VocabularyTests(BaseViewTestCase):
    @classmethod
    def setUpTestData(cls):
        logger.info(f"***** Create test data for {cls.__name__} *****")

    def setUp(self):
        # Check auth
        profile_response = self.authenticated_client.get('/users/profile/', format='json')
        if profile_response.status_code != status.HTTP_200_OK:
            logger.info(f"Login for VocabularyTests failed . Test response content: {profile_response.content}")

    def test_create_vocabulary(self):
        logger.info(f"test_create_vocabulary")
        # order_lemmas_create(sender=Vocabulary, instance=self.created_vocabulary, created=True)
        self.assertEqual(Vocabulary.objects.count(), 1)
        self.assertIsNotNone(Vocabulary.objects.get(pk=self.created_vocabulary.id).order_lemmas)
        self.assertEqual(Lemma.objects.count(), 3)
        self.assertEqual(self.created_vocabulary.title, 'Test Vocabulary')

    def test_retrieve_vocabulary(self):
        logger.info(f"test_retrieve_vocabulary")
        url = reverse('vocabulary-detail', args=[str(self.created_vocabulary.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Vocabulary')

    def test_list_vocabulary(self):
        logger.info(f"test_list_vocabulary")
        url = reverse('vocabulary-list')
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_vocabulary_languages(self):
        logger.info(f"test_list_vocabulary_languages")
        url = reverse('vocabulary-languages')
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'English')

    def test_get_vocabulary_language(self):
        logger.info(f"test_get_vocabulary_language")
        url = reverse('vocabulary-language', args=[str(self.created_vocabulary.lang_from.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'English')

    def test_patch_vocabulary(self):
        logger.info(f"test_patch_vocabulary")
        changing_data = {
            'is_active': False
        }
        url = reverse('vocabulary-detail', args=[str(self.created_vocabulary.id)])
        response = self.authenticated_client.patch(url, changing_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_active"], False)

        # Return values is_active for other tests
        response = self.authenticated_client.patch(url, {'is_active': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LemmaTests(BaseViewTestCase):
    """
    lemma_data = {
            'lemma': 'text',
            'pos': 'X',
            'translate': {},
            'vocabularies': UUID_id,
            'educations': UUID_id,
            'translate_status': <ROO, PRO, TRA>
        }
    """
    @classmethod
    def setUpTestData(cls):
        logger.info(f"***** Create test data for {cls.__name__} *****")

    def test_list_lemma(self):
        logger.info(f"test_list_lemma")
        url = reverse('lemma-list')
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_retrieve_lemma(self):
        logger.info(f"test_retrieve_lemma")
        lemma = Lemma.objects.get(lemma='test')
        url = reverse('lemma-detail', args=[str(lemma.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lemma'], 'test')

    def test_patch_lemma(self):
        logger.info(f"test_patch_lemma")
        lemma = Lemma.objects.get(lemma='test')
        changing_data = {
                         'translate_status': 'PRO'
        }
        url = reverse('lemma-detail', args=[str(lemma.id)])
        response = self.authenticated_client.patch(url, changing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["translate_status"], Lemma.TranslateStatus.IN_PROGRESS)

        # Return values is_active for other tests
        response = self.authenticated_client.patch(
            url,
            {'translate_status': Lemma.TranslateStatus.ROOKIE},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_lemma(self):
        logger.info(f"test_create_lemma")
        lemma_data = {
            'lemma': 'hello',
            'pos': 'X',
            'translate': {},
            'vocabularies': [],
            'educations': [],
            'translate_status': 'ROO'
        }

        url = reverse('lemma-list')
        response = self.authenticated_client.post(url, lemma_data, format='json')
        self.assertEqual(Lemma.objects.count(), 4)
        self.assertEqual(Lemma.objects.get(pk=str(response.data['id'])).lemma, 'hello')


if __name__ == '__main__':
    unittest.main()
