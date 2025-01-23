from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
import inspect
import config


engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)


def db_session_decorator(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        is_new = False
        session = kwargs.pop('session', None)
        if not session:
            is_new = True
            session = Session()
        try:
            return func(*args, **kwargs, session=session)
        finally:
            if is_new:
                session.close()

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        is_new = False
        session = kwargs.pop('session', None)
        if not session:
            is_new = True
            session = Session()
        try:
            return await func(*args, **kwargs, session=session)
        finally:
            if is_new:
                session.close()

    # Check if the function is a coroutine
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper