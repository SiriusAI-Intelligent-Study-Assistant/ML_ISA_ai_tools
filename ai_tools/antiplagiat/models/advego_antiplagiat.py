# -*- coding: utf-8 -*-

# pip install advego-antiplagiat-api

from antiplagiat import Antiplagiat
from antiplagiat.helpers import url_rule, domain_rule, regex_url

TOKEN = 'token' # ваш токен
api = Antiplagiat(TOKEN)

text = """
Python — высокоуровневый язык программирования общего назначения,
ориентированный на повышение производительности разработчика и читаемости кода.
Синтаксис ядра Python минималистичен.
В то же время стандартная библиотека включает большой объём полезных функций.
"""

ignore_rules = [
    domain_rule('ru.wikipedia.org'),
    url_rule('https://ru.wikipedia.org/wiki/Python'),
    regex_rule('.*wikipedia\\.org')
]

result = api.unique_text_add(text, ignore_rules=ignore_rules)
key = result['key']