from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config


engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)


def db_session_decorator(func):
    def wrapped(*args, **kwargs):
        session = Session()
        try:
            return func(*args, **kwargs, session=session)
        finally:
            session.close()
    return wrapped