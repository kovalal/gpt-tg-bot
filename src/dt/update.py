from sqlalchemy.orm import Session

from models import User, Message, Completion
from clients.db import db_session_decorator


@db_session_decorator
def set_user_model(user: User, model: str, session=None):
    user.model = model
    session.add(user)
    session.commit()
    return user

@db_session_decorator
def set_user_config(user: User, settings_name: str, settings_value, session=None):
    print(user.settings)
    user.set_settings(settings_name, settings_value)
    print(user.settings)
    session.add(user)
    session.commit()
    return user