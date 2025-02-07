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
from dt.utils import retrive_messages_from_redis, get_messages_from_pool
from bot.errors import send_error
from bot.utils import send_response
from tools import run_in_event_loop, format_and_split_message_for_telegram

from aifunctions.functioncalling import FunctionCalling
from aifunctions.gpt_llm import PromptGpt4o, PromptGpt4o_mini
from aifunctions.dallee import PromptDalle3

logger = logging.getLogger("CeleryWorker")
bot = Bot(config.BOT_TOKEN)

openai_client = OpenAIClient(api_key=config.OPENAI_KEY)

FuncCall = FunctionCalling(openai_client, tools=[PromptGpt4o, PromptGpt4o_mini, PromptDalle3])

@celery_app.task(ignore_result=True)
@run_in_event_loop
@send_error
async def process_message(clock_msg_id, from_user, message_id, text, reply_to_message, user=None, **kwargs):
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
    if reply_to_message:
        model = await define_model(reply_to_message['message_id'], chat_id, new_msgs, bot)
        ai_response = model.invoke()#openai_client.generate_completion(messages=chat, model=model)
        #assistant_response = ai_response.choices[0].message.content
        # send response from ai to user
        response_msg_pool = await model.send_response(bot, chat_id, message_id, ai_response, clock_msg_id=clock_msg_id)
        #response_msg_pool = await send_response(bot, chat_id, message_id, assistant_response, clock_msg_id=clock_msg_id)
        #completion = create_completion({**ai_response.to_dict(), 'model': model})
    else:
        chain = []
        # add last message to chain
        chain.extend(
            new_msgs
        )
        prompt = ' '.join([m.text for m in chain])
        logger.info(prompt)
                          
        executor = FuncCall.run(prompt)
        func = executor.func
        #model = func.model
        ai_response = executor()
        response_msg_pool = await func.tg_callback(bot, chat_id, message_id, ai_response, clock_msg_id=clock_msg_id)
        model = func.model_provider
    
    completion = model.get_completion(ai_response)
    #
    #logger.info(user.model)
    
    # Generate a response using OpenAI API
    #ai_response = openai_client.generate_completion(messages=chat, model=user.model)
    
    # save messages
    
    for resp_msg in response_msg_pool:
        save_message_task(**resp_msg.dict())
        msgs_to_bind.append(resp_msg.message_id)
    msgs_to_bind.extend(map(lambda m: m.id, new_msgs))
    # save completion
    save_completion(completion, msgs_to_bind)
    


