from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from models import Completion
import config
import hashlib
import json


class GPT4oAudio(BaseModel):
    """Данные об аудиоответе модели"""
    id: str  # Уникальный идентификатор аудиофайла
    expires_at: int  # Время истечения срока действия аудиофайла (Unix timestamp)
    data: str  # Base64-кодированные аудиоданные
    transcript: Optional[str] = None  # Транскрипция аудио


class GPT4oUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    completion_tokens_details: Optional[Dict[str, Any]] = None

class GPT4oChoiceMessage(BaseModel):
    role: str
    content: Optional[str] = None  # Делаем content необязательным
    audio: Optional[GPT4oAudio] = None  # Добавляем поле для аудиоданных (base64)

class GPT4oChoice(BaseModel):
    index: int
    message: GPT4oChoiceMessage
    finish_reason: str

class GPT4oResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: Optional[str] = None
    choices: List[GPT4oChoice]
    service_tier: Optional[str] = None
    usage: GPT4oUsage

    @classmethod
    def get_completion(cls, response: dict) -> Completion:
        """Создает объект Completion из JSON-ответа OpenAI"""
        gpt_response = cls(**response)  # Создаем объект GPT4oResponse из словаря
        return Completion(
            id=gpt_response.id,
            system_fingerprint=gpt_response.system_fingerprint,
            created=datetime.utcfromtimestamp(gpt_response.created),
            model=gpt_response.model,
            prompt_tokens=gpt_response.usage.prompt_tokens,
            completion_tokens=gpt_response.usage.completion_tokens,
            total_tokens=gpt_response.usage.total_tokens,
            completion_tokens_details=gpt_response.usage.completion_tokens_details,
            cost=cls.calculate_cost(gpt_response.model, gpt_response)  # Добавь свою логику расчета стоимости
        )
    
    @classmethod
    def calculate_cost(self, model, response):
        # Example cost calculation
        # Replace with your actual pricing logic
        model_name = model or config.model_config['default']
        model_pricing = config.model_config.get(model_name)
        if not model_pricing:
            raise ValueError(f"Pricing configuration not found for model: {model}")

        pricing = model_pricing['pricing']
        input_token_cost = pricing['input_tokens']
        cached_input_token_cost = pricing['cached_input_tokens']
        output_token_cost = pricing['output_tokens']

        # Extract details from completion_tokens_details
        cached_input_tokens = response.usage.completion_tokens_details.get("cached_input_tokens", 0) if response.usage.completion_tokens_details else 0

        # Calculate costs
        input_cost = (response.usage.prompt_tokens * input_token_cost) / 10 ** 6
        cached_cost = (cached_input_tokens * cached_input_token_cost) / 10 ** 6
        output_cost = (response.usage.completion_tokens * output_token_cost) / 10 ** 6

        # Assign the total cost
        return input_cost + cached_cost + output_cost


class DalleImageData(BaseModel):
    revised_prompt: str
    url: str


class DalleResponse(BaseModel):
    created: int
    data: List[DalleImageData]

    @classmethod
    def calculate_cost(self, model, response):
        # Example cost calculation
        # Replace with your actual pricing logic
        model_name = model or config.model_config['default']
        model_pricing = config.model_config.get(model_name)
        if not model_pricing:
            raise ValueError(f"Pricing configuration not found for model: {self.model}")

        pricing = model_pricing['pricing']
        return pricing['1024x1024']['Standard']

    @classmethod
    def get_completion(cls, response: dict) -> Completion:
        """Создает объект Completion из JSON-ответа OpenAI"""
        dalle_response = cls(**response)  # Создаем объект Dallee из словаря
        # Генерируем уникальный ID на основе времени и URL первой картинки
        hash_input = f"{dalle_response.created}-{dalle_response.data[0].url}".encode()
        unique_id = hashlib.sha256(hash_input).hexdigest()[:12]  # Берем первые 12 символов хэша

        return Completion(
            id=f"dalle-{unique_id}",
            system_fingerprint=None,
            created=datetime.utcfromtimestamp(dalle_response.created),
            model="dall-e-3",
            prompt_tokens=0,  # У DALL·E нет токенов
            completion_tokens=0,
            total_tokens=0,
            cost=cls.calculate_cost('dall-e-3', dalle_response)  # Здесь можно добавить свою логику расчета стоимости
        )