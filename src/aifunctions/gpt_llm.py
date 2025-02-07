from .abc import AIFunction
from abc import ABC, abstractmethod
from bot.utils import send_response
from provider.openai.llm import LlmModel


class PromptGptBase(AIFunction):

    def messages(self, prompt):
        return [{
            'role': 'user', 
            'content': [{
                'type': 'text',
                'text': prompt
            }]
        }]

    def __call__(self, task_description):
        return self.model_provider.invoke(
            messages = self.messages(task_description)
        )
    
    def tg_callback(self, bot, chat_id, message_id, ai_response, clock_msg_id):
        text = ai_response.choices[0].message.content
        return send_response(bot, chat_id, message_id, text, clock_msg_id)


class PromptGpt4o_mini(PromptGptBase):
    model = 'gpt-4o-mini'
    scheme = {
        "name": "select_model_gpt4o_mini",
        "description": "Selects the gpt4o-mini model for lightweight and simple tasks",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Brief description of the task or prompt"
                }
            },
            "additionalProperties": False,
            "required": [
                "task_description",
            ]
        }
    }


class PromptGpt4o(PromptGptBase):
    model = 'gpt-4o'
    scheme = {
        "name": "select_model_gpt4o",
        "description": "Selects the gpt4o model for medium complexity and general-purpose tasks",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
            "task_description": {
                    "type": "string",
                    "description": "Detailed description of the task or prompt"
                },
            },
            "additionalProperties": False,
            "required": [
                "task_description",
            ]
        }
    }
