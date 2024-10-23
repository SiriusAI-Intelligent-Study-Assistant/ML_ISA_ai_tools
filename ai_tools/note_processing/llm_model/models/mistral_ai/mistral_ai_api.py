# -*- coding: utf-8 -*-
# https://mistral.ai/

from mistralai import Mistral
import logging

# TODO: Как позаботиться о безопасности данных? Чтобы пользователи не вводили запрещённое
class MistralAI_API:
    '''
    Class for working with Mistral API
    '''

    def __init__(self, api_key: str) -> None:
        self.history = str

        self.model = "mistral-large-latest"
        try:
            self.client = Mistral(api_key=api_key)
            logging.info("Mistral_API connected")
        except Exception as e:
            logging.error(repr(e))
            raise

    def load_history(self, history_path: str) -> None:
        with open(history_path, "r") as file:
            self.history = file.read()

    def save_history(self, history_path: str) -> int:
        with open(history_path, "w") as file:
            return file.write(self.history)
        
    def get_history(self) -> str:
        return self.history

    def set_history(self, history: str) -> None:
        self.history = history
        
    def set_prompt(self, initial_prompt: str) -> None:
        self.history = initial_prompt
    
    def chat_with_llm(self, content: str, user_name: str="User: ", role: str='user') -> str:
        try:
            self.history = self.history + "\n" + user_name + content
            self.chat_response = self.client.chat.complete(
                model = self.model,
                messages = [
                    {
                        "role": role,
                        "content": self.history,
                    },
                ]
            )
            
            self.answer = self.chat_response.choices[0].message.content
            self.history = self.history + "\n" + self.answer
            logging.info(f"Successfully received a response to the request: {content}")
            return self.answer
        
        except Exception as e:
            logging.error(self.history + " | " + repr(e))
            raise