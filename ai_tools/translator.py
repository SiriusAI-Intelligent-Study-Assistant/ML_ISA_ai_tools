# -*- coding: utf-8 -*-

from translate import Translator


def translate(from_lang: str, to_lang: str, text: str) -> str:
    '''
    The function uses the “translate” library,
    which accesses a service (mymemory, microsoft, deepl, libre)
    via API to translate a piece of text from one language to another

    Example: translate("ru", "en", "Привет, мир!")\n
    Exceptions: ConnectionError
    '''

    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    try:
        translation = translator.translate(text)
        return translation

    except:
        raise ConnectionError