from .abc import AIFunction
from abc import ABC, abstractmethod
from bot.utils import send_response, send_audio_response
from provider.openai.llm import LlmModel, GptModel, GptAudioModel


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
    
    async def tg_callback(self, bot, chat_id, message_id, ai_response, clock_msg_id):
        #text = ai_response.choices[0].message.content
        #return send_response(bot, chat_id, message_id, text, clock_msg_id)
        return await self.model_provider.send_response(bot, chat_id, message_id, ai_response, clock_msg_id)


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


class PromptGpt4o_mini_audio(PromptGptBase):
    model = 'gpt-4o-mini-audio-preview'
    scheme = {
        "name": "select_model_gpt-4o-mini-audio-preview",
        "description": "Selects the gpt4o-mini model for lightweight and simple tasks demanding audio generation",
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

    def __call__(self, task_description):
        return self.model_provider.invoke(
            messages = self.messages(task_description),
            modalities = ["text", "audio"],
            audio = {'voice': "alloy", 'format': "wav" }
        )
    
    #def tg_callback(self, bot, chat_id, message_id, ai_response, clock_msg_id):
    #    audio = ai_response.choices[0].message.audio.data
    #    text = ai_response.choices[0].message.audio.transcript
    #    return send_audio_response(bot, chat_id, message_id, audio, text, clock_msg_id)