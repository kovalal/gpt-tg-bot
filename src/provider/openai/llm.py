import config
from .client import OpenAIClient
from .obj import GPT4oResponse, DalleResponse
from abc import ABC, abstractmethod
from dt.retrive import retrive_chain
from clients.db import Session
from bot.utils import send_response, send_image_response


class OpenAIModelBase(ABC):
    client = OpenAIClient(api_key=config.OPENAI_KEY)
    
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

    def get_completion(self, api_response):
        return GPT4oResponse.get_completion(api_response.to_dict()|{'model': self.model})


class GptModel(OpenAIModelBase):

    async def add_context(self, chain, bot):
        self.chat = [await m.gpt_repr(bot) for m in chain]
        return self.chat

    async def send_response(self, bot, chat_id, message_id, ai_response, clock_msg_id=None):
        text = ai_response.choices[0].message.content
        return await send_response(bot, chat_id, message_id, text, clock_msg_id=clock_msg_id)

    def invoke(self, messages=None):        
        return self.client.generate_completion(messages=messages or self.chat, model=self.model)
    

class OpenaiDalee(OpenAIModelBase):
    args = []
    kwargs = {}

    async def add_context(self, chain, bot):
        print(chain)
        self.prompt = '\n'.join([m.text for m in chain])

    def invoke(self, prompt=None):
        return self.client.generate_image(prompt=prompt or self.prompt, *self.args, model=self.model, **self.kwargs)
    
    def get_completion(self, api_response):
        print(api_response)
        return DalleResponse.get_completion(api_response.to_dict()|{'model': self.model})
    
    async def send_response(self, bot, chat_id, message_id, ai_response, clock_msg_id=None):
        url = ai_response.data[0].url
        text = ai_response.data[0].revised_prompt
        return await send_image_response(bot, chat_id, message_id, url, clock_msg_id, text)
    
    
class LlmModel():
    def __new__(cls, model=None):
        model_name = model or config.model_config['default']
        print(model_name)
        if model_name in ['gpt-4o', 'gpt-4o-mini']:
            return GptModel(model_name)
        elif model_name in ['dall-e-3']:
            return OpenaiDalee(model_name)


async def define_model(message_id, chat_id, new_msgs, bot):
    with Session() as session:
        chain = retrive_chain(message_id, chat_id, session=session)
        chain.extend(new_msgs)  
        model = LlmModel(chain[0].completion.model)
        await model.add_context(chain, bot)
    return model