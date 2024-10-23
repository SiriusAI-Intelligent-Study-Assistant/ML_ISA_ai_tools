# -*- coding: utf-8 -*-

import unittest

import sys
sys.path.append('..')
import ai_tools
sys.path.clear()

class TestAiTools(unittest.TestCase):
    #setUp method is overridden from the parent class TestCase
    def setUp(self):
        ...
        
    def test_translator_ru_en(self):
        self.assertEqual(ai_tools.translate('ru', 'en', 'Привет, мир!'), 'Hello, world!')
    def test_translator_en_ru(self):
        self.assertEqual(ai_tools.translate('en', 'ru', 'Hello, world!'), 'Привет, мир!')
  
# Executing the tests in the above test case class
if __name__ == "__main__":
    unittest.main()

# TODO: Добавить тесты на CreateLLMSession!!! Нужны ли они?