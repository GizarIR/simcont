# TODO Create your tests here.
#  https://www.django-rest-framework.org/api-guide/testing/#testing
#  https://chat.openai.com/c/709f23ba-47c8-4d27-aa58-2c1d1655003c

import unittest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from drf_app.langutils import SimVoc


class LangUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.lemmas_dict = {'lemma1': 5, 'lemma2': 4, 'lemma3': 1}

    @patch('drf_app.langutils.logger.info')
    def test_print_order_lemmas_console(self, mock_logger_info):
        instance = SimVoc()
        instance.print_order_lemmas_console(self.lemmas_dict, limit=2)
        expected_calls = [unittest.mock.call('lemma1: 5'), unittest.mock.call('lemma2: 4')]
        mock_logger_info.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()