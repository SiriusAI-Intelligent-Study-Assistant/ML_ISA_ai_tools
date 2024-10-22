#import fitz
import nltk
import string
import pymorphy3

# загружаем словари и правила для pymorphy2
morph = pymorphy3.MorphAnalyzer()

# загружаем русский язык для NLTK
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('tagsets')
nltk.download('words')
nltk.download('maxent_ne_chunker')
nltk.download('stopwords')
nltk.download('punkt_tab')

# извлекаем текст из PDF-файла
'''
with fitz.open('example.pdf') as doc:
    text = ""
    for page in doc:
        text += page.getText()
'''

text = "Пвриет, как у тебя дела Спешу щзаписать лекуифю Не могу остановиться ЛОектро бюыстрый шибко"

# токенизируем текст и удаляем пунктуацию
tokens = nltk.word_tokenize(text)
tokens = [word for word in tokens if word.isalnum()]

# исправляем орфографические ошибки
corrected_tokens = []
for token in tokens:
    parsed_token = morph.parse(token)[0]
    if 'LATIN' in parsed_token.tag or 'PNCT' in parsed_token.tag:
        corrected_tokens.append(token)
    else:
        corrected_tokens.append(parsed_token.normal_form)

# восстанавливаем пунктуацию
final_text = ""
for i, token in enumerate(corrected_tokens):
    final_text += token
    if i < len(corrected_tokens) - 1 and corrected_tokens[i+1] not in string.punctuation:
        final_text += " "
    elif i < len(corrected_tokens) - 1 and corrected_tokens[i+1] in string.punctuation:
        final_text += corrected_tokens[i+1]

print(final_text)