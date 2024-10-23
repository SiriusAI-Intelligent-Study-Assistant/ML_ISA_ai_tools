# -*- coding: utf-8 -*-

import logging
logging.basicConfig(level=logging.INFO, 
                    filename="log.log", 
                    filemode="a", 
                    format="[%(asctime)s %(levelname)s]: %(message)s")

from .translator import translate
from .note_processing.create_llm_session import CreateLLMSession
from .config import *

__version__ = '0.0.1'