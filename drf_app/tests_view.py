import json
import os
import time
import unittest
from urllib.parse import urlencode

from django.db.models.signals import post_save
from django.urls import reverse
from rest_framework import status

from drf_app.langutils import SimVoc
from drf_app.models import Lang, Vocabulary, Lemma, Education, Board
from drf_app.signals import order_lemmas_create, translate_lemma_signal
from drf_app.tasks import create_order_lemmas_async, translate_lemma_async

import logging

from drf_app.views import LemmaViewSet
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
            'source_text': 'Tests Source Text Test',
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

        # check: is there this lemma in Lemma's model
        response = self.authenticated_client.post(url, lemma_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'This lemma already exists. Please use the existing ID instead of creating a new entry.'
        )

    def test_delete_lemma(self):
        logger.info(f"test_delete_lemma")
        lemma_data = {
            'lemma': 'frog',
            # 'pos': 'X',
            # 'translate': {},
            # 'vocabularies': [],
            # 'educations': [],
            # 'translate_status': 'ROO'
        }

        lemma = Lemma.objects.create(**lemma_data)
        lemma.vocabularies.add(Vocabulary.objects.first(), through_defaults={"frequency": 0})
        lemma.save()

        url = reverse('lemma-detail', args=[str(lemma.id)])
        response = self.authenticated_client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lemma.objects.count(), 3)
        self.assertEqual(Lemma.objects.filter(pk=str(lemma.id)).exists(), False)

    def test_translate_lemma(self):
        logger.info(f"test_translate_lemma")
        lemma = Lemma.objects.all().first()

        post_save.disconnect(translate_lemma_signal, sender=LemmaViewSet)

        url = reverse('lemma-translate', args=[str(lemma.id)])
        response = self.authenticated_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post_save.connect(translate_lemma_signal, sender=LemmaViewSet)

    def test_get_id_lemma_by_token(self):
        logger.info(f"test_get_id_lemma_by_token")

        phrase = self.vocabulary_data["source_text"][:5].lower()
        query_params = urlencode({'token': phrase})

        url = reverse('lemma-get-id-lemma-by-token') + '?' + query_params
        response = self.authenticated_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lemma"], SimVoc.get_token(phrase)[0].lemma_)


class EducationTests(BaseViewTestCase):
    @classmethod
    def setUpClass(cls):
        logger.info(f"***** Create test data for {cls.__name__} *****")
        super().setUpClass()

        cls.education_data = {
            'vocabulary': str(cls.created_vocabulary.id),
            'limit_lemmas_item': 1,
            'limit_lemmas_period': 2,
        }

        url_edu = reverse('education-list')
        response_edu = cls.authenticated_client.post(url_edu, cls.education_data, format='json')
        cls.created_education = Education.objects.get(pk=response_edu.json()['id'])
        cls.create_education_status = response_edu.status_code

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up any data as needed
        cls.created_education.delete()

    def test_create_education(self):
        logger.info(f"test_create_education")
        self.assertEqual(self.create_education_status, status.HTTP_201_CREATED)
        self.assertEqual(Education.objects.count(), 1)
        self.assertEqual(Board.objects.count(), 1)

    def test_list_education(self):
        logger.info(f"test_list_education")
        url = reverse('education-list')
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_education(self):
        logger.info(f"test_retrieve_education")
        url = reverse('education-detail', args=[str(self.created_education.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_finished'])

    def test_patch_education(self):
        logger.info(f"test_patch_education")
        changing_data = {
                         'is_finished': True
        }
        url = reverse('education-detail', args=[str(self.created_education.id)])
        response = self.authenticated_client.patch(url, changing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_finished"])

        # Return values is_active for other tests
        response = self.authenticated_client.patch(
            url,
            {'is_finished': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_education(self):
        logger.info(f"test_delete_education")
        education_data = {
            'vocabulary': self.created_vocabulary,
            'learner': self.user,
        }

        education = Education.objects.create(**education_data)
        education.save()
        self.assertEqual(Education.objects.count(), 2)

        url = reverse('education-detail', args=[str(education.id)])
        response = self.authenticated_client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Education.objects.count(), 1)
        self.assertEqual(Education.objects.filter(pk=str(education.id)).exists(), False)


class BoardTests(BaseViewTestCase):
    @classmethod
    def setUpClass(cls):
        logger.info(f"***** Create test data for {cls.__name__} *****")
        super().setUpClass()
        cls.education_data = {
            'vocabulary': str(cls.created_vocabulary.id),
            'limit_lemmas_item': 1,
            'limit_lemmas_period': 2,
        }

        url_edu = reverse('education-list')
        response_edu = cls.authenticated_client.post(url_edu, cls.education_data, format='json')
        cls.created_education = Education.objects.get(pk=response_edu.json()['id'])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up any data as needed
        cls.created_education.delete()

    def test_create_board(self):
        logger.info(f"test_create_board")
        self.assertEqual(Board.objects.count(), 1)

        board_data = {
            'education': str(self.created_education.id),
        }

        url = reverse('board-list')
        response = self.authenticated_client.post(url, board_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Board.objects.count(), 2)
        self.assertIsNone(Board.objects.get(pk=str(response.data['id'])).set_lemmas)

    def test_list_boards(self):
        logger.info(f"test_list_boards")
        url = reverse('board-list')
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_board(self):
        logger.info(f"test_retrieve_board")
        board = Board.objects.first()
        url = reverse('board-detail', args=[str(board.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['set_lemmas'])

    def test_delete_board(self):
        logger.info(f"test_delete_board")
        board_data = {
            'education': self.created_education,
        }

        board = Board.objects.create(**board_data)
        board.save()
        self.assertEqual(Board.objects.count(), 2)

        url = reverse('board-detail', args=[str(board.id)])
        response = self.authenticated_client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Board.objects.count(), 1)
        self.assertEqual(Board.objects.filter(pk=str(board.id)).exists(), False)

    def test_get_study_status(self):
        logger.info(f"test_get_study_status")
        education = self.created_education
        board = Board.objects.filter(education=education)[0]
        id_lemma = json.loads(board.set_lemmas)['1'][0]

        # url = reverse('board-get-study-status', kwargs={'pk': str(board.id)})
        # url += f'?id_lemma={id_lemma}'
        # or
        query_params = urlencode({'id_lemma': id_lemma})
        url = reverse('board-get-study-status', kwargs={'pk': str(board.id)}) + '?' + query_params

        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'NE')

    def test_set_study_status(self):
        logger.info(f"test_set_study_status")
        education = self.created_education
        board = Board.objects.filter(education=education)[0]
        id_lemma = json.loads(board.set_lemmas)['1'][0]

        changing_data = {
            'status': 'ST',
            'id_lemma': id_lemma
        }

        url = reverse('board-set-study-status', args=[str(board.id)])
        response = self.authenticated_client.patch(url, changing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], 'ST')

        # Return values is_active for other tests
        response = self.authenticated_client.patch(
            url,
            {'status': 'NE', 'id_lemma': id_lemma},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], 'NE')

    def test_update_set_lemmas(self):
        logger.info(f"test_update_set_lemmas")
        board = Board.objects.first()
        url = reverse('board-update-set-lemmas', args=[str(board.id)])
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['set_lemmas'])


if __name__ == '__main__':
    unittest.main()
