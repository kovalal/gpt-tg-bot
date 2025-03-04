import config
from .client import OpenAIClient
from .obj import GPT4oResponse, DalleResponse
from abc import ABC, abstractmethod
from dt.retrive import retrive_chain
from clients.db import Session
from bot.utils import send_response, send_image_response, send_audio_response
from tools import retrieve_image_base64
from bot.errors import UserException


class OpenAIModelBase(ABC):
    client = OpenAIClient(api_key=config.OPENAI_KEY)
    response_srlz_class = GPT4oResponse
    
    def __init__(self, model):
        self.model = model
        self.price = config.model_config.get(self.model)

    @abstractmethod
    async def add_context(self, chain, bot):
        pass

    @abstractmethod
    def invoke(self, messages):
        pass
    
    @abstractmethod
    async def send_response(self, *args, **kwargs):
        pass
    
    async def gpt_repr(self, msg, bot=None):
        content = []
        if msg.completion:
            text = ''.join([m.text for m in msg.completion.messages if self.user == m.user])
            content.append({"type": "text", "text": text})
        else:
            content.append({"type": "text", "text": msg.text})

        # Include the image content if it exists
        if msg.image_file_id and bot:
            base64_image = await retrieve_image_base64(bot, msg.image_file_id)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        return {"content": content, "role": msg.get_role()}

    def get_completion(self, api_response):
        return self.response_srlz_class.get_completion(api_response.to_dict()|{'model': self.model})


class GptModelBase(OpenAIModelBase, ABC):

    async def send_response(self, bot, chat_id, message_id, ai_response, clock_msg_id=None):
        text = ai_response.choices[0].message.content
        return await send_response(bot, chat_id, message_id, text, clock_msg_id=clock_msg_id)

    def invoke(self, messages=None, **kwargs):        
        return self.client.generate_completion(messages=messages or self.chat, model=self.model, **kwargs)


class GptModel(GptModelBase):
    async def add_context(self, chain, bot):
        self.chat = [await self.gpt_repr(m, bot) for m in chain]
        return self.chat
    

class GptReasoningModel(GptModelBase):
    async def add_context(self, chain, bot):
        for msg in chain:
            if msg.image_file_id:
                raise UserException("Данная модель не может работать с изображениями")
            await self.gpt_repr(msg, bot)
        self.chat = [await self.gpt_repr(m, bot) for m in chain]
        return self.chat
    


class GptAudioModel(OpenAIModelBase):
    kwargs = {
        'modalities': ["text", "audio"],
        'audio': {'voice': "alloy", 'format': "wav" }
    }

    async def add_context(self, chain, bot):
        self.chat = [await m.gpt_repr(bot) for m in chain]
        return self.chat

    async def send_response(self, bot, chat_id, message_id, ai_response, clock_msg_id=None):
        audio = ai_response.choices[0].message.audio.data
        text = ai_response.choices[0].message.audio.transcript
        return await send_audio_response(bot, chat_id, message_id, audio, text, clock_msg_id)

    def invoke(self, messages=None, **kwargs):
        kwargs = self.kwargs | kwargs    
        return self.client.generate_completion(messages=messages or self.chat, model=self.model, **kwargs)
    

class OpenaiDalee(OpenAIModelBase):
    args = []
    kwargs = {}

    async def add_context(self, chain, bot):
        print(chain)
        self.prompt = '\n'.join([m.text for m in chain])

    def invoke(self, prompt=None):
        return self.client.generate_image(prompt=prompt or self.prompt, *self.args, model=self.model, **self.kwargs)
    
    def get_completion(self, api_response):
        return DalleResponse.get_completion(api_response.to_dict()|{'model': self.model})
    
    async def send_response(self, bot, chat_id, message_id, ai_response, clock_msg_id=None):
        url = ai_response.data[0].url
        text = ai_response.data[0].revised_prompt
        return await send_image_response(bot, chat_id, message_id, url, clock_msg_id, text)
    

class OpenaiWhisper(OpenAIModelBase):
    def add_context(self, chain, bot):
        raise NotImplementedError()

    def invoke(self, audio=None):
        return self.client.transcribe(model="whisper-1", file=audio)

    def send_response(self, *args, **kwargs):
        raise NotImplementedError()


class LlmModel():
    def __new__(cls, model=None):
        model_name = model or config.model_config['default']
        if model_name in ['gpt-4o', 'gpt-4o-mini']:
            return GptModel(model_name)
        elif model_name in ['o1', 'o3-mini']:
            return GptReasoningModel(model_name)
        elif model_name in ['gpt-4o-mini-audio-preview']:
            return GptAudioModel(model_name)
        elif model_name in ['dall-e-3']:
            return OpenaiDalee(model_name)
        elif model_name in ['whisper']:
            return OpenaiWhisper(model_name)


async def define_model(message_id, chat_id, new_msgs, bot):
    with Session() as session:
        chain = retrive_chain(message_id, chat_id, session=session)
        chain.extend(new_msgs)  
        model = LlmModel(chain[0].completion.model)
        await model.add_context(chain, bot)
    return model