import redis
import json
from functools import partial
from sqlalchemy.orm import Session

from models import User, Message, Completion
from clients.db import db_session_decorator
from clients.redis import redis_client

from .create import create_message


@db_session_decorator
def get_user_or_create(id, username, first_name, last_name, is_bot, language_code, is_premium, session=None, **kwargs):
    user = session.query(User).filter_by(id=id).first()
    if not user:
        user = User(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_bot=is_bot,
            language_code=language_code,
            is_premium=is_premium,
        )
        session.add(user)
        session.commit()
    return user


def retrive_messages_from_redis(user_id: str):
    cache_key = f"user:{user_id}:messages"
    messages = redis_client.lrange(cache_key, 0, -1)
    if not messages:
        return []
    redis_client.delete(cache_key)
    return [json.loads(msg.decode('utf-8')) for msg in messages]


def save_msg_redis(tg_msg, expire=5):
    user_id = tg_msg['from_user']['id']
                #message_id = event.message_id
                #timestamp = event.date.timestamp()
    cache_key = f"user:{user_id}:messages"
    # Append the message to the Redis cache
    if isinstance(tg_msg, dict):
        event_str = json.dumps(tg_msg, indent=4, sort_keys=True, default=str)
    else:
        event_str = json.dumps(tg_msg.dict(), indent=4, sort_keys=True, default=str)
    redis_client.rpush(cache_key, event_str)
    redis_client.expire(cache_key, expire)  # Set expiration 
    return cache_key


def get_messages_from_pool(chat_id: int, user: User) -> list[dict]:
    """collect messages from cache"""
    #msg_pool = retrive_messages_from_redis(chat_id)
    #if msg_pool:
    #    coros = [create_message(msg, user).gpt_repr(bot) for msg in msg_pool]
        #last_msg = [await c for c in coros]
    return [create_message(msg, user) for msg in retrive_messages_from_redis(chat_id)]


def get_text_from_user(user_id: str):
    msg_pool = retrive_messages_from_redis(user_id)
    return ''.join([msg['text'] for msg in msg_pool])