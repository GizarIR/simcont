# TODO Create your tests here.
#  https://www.django-rest-framework.org/api-guide/testing/#testing
#  https://chat.openai.com/c/709f23ba-47c8-4d27-aa58-2c1d1655003c
import os
import unittest

import fitz
from django.test import TestCase
from unittest.mock import patch, MagicMock
from drf_app.langutils import SimVoc


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

    def tearDown(self):
        # For test_convert_to_txt_txt_file
        project_directory = os.path.dirname(os.path.abspath(__file__))
        txt_file_path = os.path.join(project_directory, 'test_file.txt')
        pdf_file_path = os.path.join(project_directory, 'test_file.pdf')
        os.remove(txt_file_path)
        os.remove(pdf_file_path)

    @patch('drf_app.langutils.logger.info')
    def test_print_order_lemmas_console(self, mock_logger_info):
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
        instance = SimVoc()
        txt_file_path = self.built_test_path_file('test_file.txt')

        with open(txt_file_path, 'rb') as txt_file:
            result = instance.convert_to_txt(txt_file)

        expected_result = "Test content for txt file."
        self.assertEqual(result, expected_result)

        mock_logger_info.assert_called_once_with(f"Func convert_to_txt starts to read file {txt_file_path}.")

    @patch('drf_app.langutils.logger.info')
    def test_convert_to_txt_pdf_file(self, mock_logger_info):
        instance = SimVoc()
        pdf_file_path = self.built_test_path_file('test_file.pdf')

        with open(pdf_file_path, 'rb') as pdf_file:
            result = instance.convert_to_txt(pdf_file)

        expected_result = "Test content for pdf file."
        self.assertEqual(result, expected_result)

        mock_logger_info.assert_called_once_with(f"Func convert_to_txt starts to read file {pdf_file_path}.")

    @patch('drf_app.langutils.logger.info')
    def test_clean_text(self, mock_logger):
        input_text = "Hello, 123 world!\nThis is a test1."
        expected_output = "Hello world This is test"

        cleaned_text = SimVoc.clean_text(input_text)

        self.assertEqual(cleaned_text, expected_output)


if __name__ == '__main__':
    unittest.main()
