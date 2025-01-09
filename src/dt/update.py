from sqlalchemy.orm import Session

from models import User, Message, Completion
from clients.db import db_session_decorator


@db_session_decorator
def set_user_model(user, model, session=None):
    user.model = model
    session.add(user)
    session.commit()