# -*- coding: utf-8 -*-

import logging
from .llm_model import MistralAI_API,\
                       SUMMARIZATION_PROMPT,\
                       PARAPHRASING_PROMPT,\
                       CHAT_PROMPT


class CreateLLMSession:
    '''
    Creates a session with the LLM. Gives access to LLM functions
    '''

    def __init__(self, model_config: dict) -> None:
        self.chat_history = CHAT_PROMPT

        match model_config["model_name"]:
            case "mistral":
                self.model = MistralAI_API(model_config["API_KEY"])
            case "GigaChat":
                self.model = MistralAI_API(model_config["API_KEY"])
            case _:
                raise NameError("Incorrect model name")
            
    def summarize(self, text: str) -> str:
        self.model.set_history('')
        self.model.set_prompt(SUMMARIZATION_PROMPT)
        try:
            return self.model.chat_with_llm(text)
        except Exception as e:
            logging.error(f"[summarize]: {text}, type: {type(text)}" + " | " + repr(e))
            raise
    
    def paraphrase(self, text: str) -> str:
        self.model.set_history('')
        self.model.set_prompt(PARAPHRASING_PROMPT)
        try:
            return self.model.chat_with_llm(text)
        except Exception as e:
            logging.error(f"[paraphrase]: {text}, type: {type(text)}" + " | " + repr(e))
            raise
    
    def chat(self, text: str) -> str:
        self.model.set_history(self.chat_history)
        try:
            self.model_answer = self.model.chat_with_llm(text)
            self.chat_history = self.model.get_history()
            logging.info(f'[chat]: Text: "{text}", Answer: "{self.model_answer}"')
            return self.model_answer
        except Exception as e:
            logging.error(f'[chat]: "{text}", type: {type(text)}' + ' | ' + repr(e))
            raise