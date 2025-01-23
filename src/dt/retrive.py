from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import joinedload

import models 
import config

from clients.db import db_session_decorator


def retrive_message(message_id, chat_id, session=None, bot=None):
    return session\
        .query(models.Message)\
        .options(joinedload(models.Message.user))\
        .options(joinedload(models.Message.completion))\
        .filter_by(chat_id=chat_id, id=message_id).first()


@db_session_decorator
def retrive_user(user_id, session=None):
    return session.query(models.User).filter_by(id=user_id).first()


@db_session_decorator
def retrive_chain(message_id, chat_id, session=None):
    last = retrive_message(message_id, chat_id, session=session)
    chain = [last]
    while last.reply_to_message:
        last = retrive_message(last.reply_to_message, chat_id, session=session)
        chain.append(last)
    return chain[::-1]
    

@db_session_decorator
def retrive_last_response_to_user(user_id, session=None):
    # Находим последнего пользователя-бота, отправившего сообщение пользователю
    last_response = (
        session.query(models.Message)
        .join(models.User, models.User.id == models.Message.user_id)
        .filter(models.User.is_bot == True, models.Message.chat_id == user_id)
        .order_by(models.Message.date.desc())  # Сортировка по убыванию даты
        .first()
    )

    return last_response