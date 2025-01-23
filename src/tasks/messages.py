from celery_app import celery_app
from aiogram import Bot, types
from aiogram.enums.parse_mode import ParseMode

import logging
import asyncio
import time

import config
from clients.gpt import OpenAIClient, replica_repr
from clients.db import Session
from tasks.database import save_message_task
from dt.retrive import retrive_chain, retrive_user
from dt.create import save_completion, create_message
from dt.utils import retrive_messages_from_redis, get_messages_from_pool
from bot.errors import send_error
from tools import run_in_event_loop, format_and_split_message_for_telegram

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
    user = retrive_user(user['id'])
    logger.info(f"Processing message from user {chat_id}: {reply_to_message}")
    #collect simultenious messages
    new_msgs = get_messages_from_pool(chat_id, user)
    #collect chain of messages
    chain = []
    with Session() as session:
        if reply_to_message:
            chain = retrive_chain(reply_to_message['message_id'], chat_id, session=session)
        
        # add last message to chain
        chain.extend(
            new_msgs
        )
        chat = [await m.gpt_repr(bot) for m in chain]
    logger.info(chat)
    logger.info(user.model)
    # Generate a response using OpenAI API
    ai_response = openai_client.generate_completion(messages=chat, model=user.model)
    assistant_response = ai_response.choices[0].message.content
    # send response from ai to user
    response_msg_pool = await send_response(chat_id, message_id, assistant_response, clock_msg_id=clock_msg_id)
    # save messages
    msgs_to_bind = [message_id]
    for resp_msg in response_msg_pool:
        save_message_task(**resp_msg.dict())
        msgs_to_bind.append(resp_msg.message_id)
    msgs_to_bind.extend(map(lambda m: m.id, new_msgs))
    # save completion
    save_completion({**ai_response.to_dict(), 'model': user.model or config.model_config['default']},
                    msgs_to_bind)
    

async def send_response(chat_id, message_id, text, clock_msg_id=None):
    """
    Send response 
    """
    msgs = format_and_split_message_for_telegram(text)
    sent_messages = []  # To store the message objects

    if clock_msg_id:
        await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)

    # Send each message in the list
    for msg in msgs:
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=message_id,
            reply_markup=types.ForceReply() if msg == msgs[-1] else None  # ForceReply only for the last message
        )
        logger.info(sent_message)
        sent_messages.append(sent_message)

    return sent_messages
