# -*- coding: utf-8 -*-

from translate import Translator
import logging


def translate(from_lang: str, to_lang: str, text: str) -> str:
    '''
    The function uses the “translate” library,
    which accesses a service (mymemory, microsoft, deepl, libre)
    via API to translate a piece of text from one language to another

    Example: translate("ru", "en", "Привет, мир!")
    '''

    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    try:
        translation = translator.translate(text)
        logging.info(f'Translate "{text}" --> "{translation}" from <{from_lang}> to <{to_lang}>')
        return translation

    except Exception as e:
        logging.error(repr(e))
        raise