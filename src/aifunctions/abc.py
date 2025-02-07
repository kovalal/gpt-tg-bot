from abc import ABC, abstractmethod
from provider.openai.llm import LlmModel

class AIFunction(ABC):
    def __init__(self, client):
        self.client = client
        self.model_provider = LlmModel(self.model)

    @classmethod
    def name(cls):
        return cls.scheme['name']

    @abstractmethod
    def __call__(self, *args, **kwds):
        pass

    @abstractmethod
    def tg_callback(self, *args, **kwargs):
        pass