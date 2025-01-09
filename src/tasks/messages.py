from celery_app import celery_app
from aiogram import Bot, types

import logging
import asyncio
import time

import config
from clients.gpt import OpenAIClient, replica_repr
from tasks.database import save_message_task
from dt.retrive import retrive_chain
from dt.create import save_completion
from dt.utils import retrive_messages_from_redis
from bot.errors import send_error
from tools import run_in_event_loop

logger = logging.getLogger("CeleryWorker")
bot = Bot(config.BOT_TOKEN)

openai_client = OpenAIClient(api_key=config.OPENAI_KEY)


@celery_app.task(ignore_result=True)
@run_in_event_loop
@send_error
async def process_message(clock_msg_id, from_user, message_id, text, reply_to_message, user=None, **kwargs):
    """
    Process the user's message and send a response via Telegram.
    """
    chat_id = from_user['id']

    logger.info(f"Processing message from user {chat_id}: {reply_to_message}")
    #collect simultenious messages
    msg_pool = retrive_messages_from_redis(chat_id)
    if msg_pool:
        text = ''.join([msg['text'] for msg in msg_pool])
    #collect chain of messages
    chain = []
    if reply_to_message:
        chain = retrive_chain(reply_to_message['message_id'], chat_id)
    
    # add last message to chain
    chain.append(
        replica_repr(text, 'user')
    )

    # Generate a response using OpenAI API
    ai_response = openai_client.generate_completion(messages=chain, model=user['model'])
    assistant_response = ai_response.choices[0].message.content
    # send response from ai to user
    response_msg = await send_response(chat_id, message_id, assistant_response, clock_msg_id=clock_msg_id)
    # save messages
    save_message_task(**response_msg.dict())
    msgs_to_bind = [message_id, response_msg.message_id] + [msg['message_id'] for msg in msg_pool]
    # save completion
    save_completion({**ai_response.to_dict(), 'model': user['model'] or config.model_config['default']},
                    msgs_to_bind)
    

async def send_response(chat_id, message_id, text, clock_msg_id=None):
    """
    Send response 
    """
    if clock_msg_id:
        await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)
    return await bot.send_message(chat_id=chat_id, text=text, 
                                  reply_to_message_id=message_id, reply_markup=types.ForceReply())