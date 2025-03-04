from celery_app import celery_app
from aiogram import Bot, types

import logging

import config
from provider.openai.client import OpenAIClient
from clients.db import Session
from provider.openai.llm import LlmModel, define_model
from provider.openai.obj import GPT4oResponse
from tasks.database import save_message_task
from dt.retrive import retrive_chain, retrive_user
from dt.create import save_completion, create_message, create_completion
from dt.utils import retrive_messages_from_redis, get_messages_from_pool, save_msg_redis
from bot.errors import send_error
from bot.utils import send_response, delete_notify_decorator
from tools import run_in_event_loop, format_and_split_message_for_telegram, retrieve_audio

from aifunctions.functioncalling import FunctionCalling
from aifunctions.gpt_llm import PromptGpt4o, PromptGpt4o_mini, PromptGpt4o_mini_audio
from aifunctions.dallee import PromptDalle3

logger = logging.getLogger("CeleryWorker")
bot = Bot(config.BOT_TOKEN)

openai_client = OpenAIClient(api_key=config.OPENAI_KEY)

FuncCall = FunctionCalling(openai_client, tools=[PromptGpt4o, PromptGpt4o_mini, PromptDalle3, PromptGpt4o_mini_audio])


@celery_app.task(ignore_result=True)
@run_in_event_loop
@send_error
@delete_notify_decorator(bot)
async def process_message(from_user, message_id, text, reply_to_message, user=None, **kwargs):
    """
    Process the user's message and send a response via Telegram.
    """
    chat_id = from_user['id']
    user = retrive_user(user['id'])
    logger.info(f"Processing message from user {chat_id}: {reply_to_message}")
    #collect simultenious messages
    new_msgs = get_messages_from_pool(chat_id, user)
    #collect chain of messages
    msgs_to_bind = [message_id]
    model_name = user.model or 'auto'
    chain = []
            # add last message to chain
    chain.extend(
        new_msgs
    )
    
    if model_name == 'auto':
        if reply_to_message:
            model = await define_model(reply_to_message['message_id'], chat_id, new_msgs, bot)
            #await model.add_context(chain, bot)
            ai_response = model.invoke()
        else:
            msgs = [await m.gpt_repr(bot) for m in chain]        
            executor = FuncCall.run(msgs)
            model = executor.func.model_provider
            ai_response = executor()       
    else:
        model = LlmModel(model_name)
        await model.add_context(chain, bot)
        ai_response = model.invoke()
        
    response_msg_pool = await model.send_response(bot, chat_id, message_id, ai_response)
    completion = model.get_completion(ai_response)
    
    for resp_msg in response_msg_pool:
        save_message_task(**resp_msg.dict())
        msgs_to_bind.append(resp_msg.message_id)
    msgs_to_bind.extend(map(lambda m: m.id, new_msgs))
    # save completion
    save_completion(completion, msgs_to_bind)
    

@celery_app.task(ignore_result=True)
@run_in_event_loop
@send_error
async def transcribe_voice(message: types.Message, **kwargs):
    user_id = message['from_user']['id']
    model = LlmModel('whisper')
    audio = await retrieve_audio(bot, message['voice']['file_id'])
    audio.name = 'audio.ogg'
    ai_response = model.invoke(audio)
    message['text'] = ai_response.text
    retrive_messages_from_redis(user_id)
    save_msg_redis(message, 5)
    process_message.delay(**message, **kwargs)

