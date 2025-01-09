import redis
import json
from aiogram import BaseMiddleware
from aiogram.types import Message

from tasks.database import save_message_task  # Celery task for saving messages
from dt.utils import get_user_or_create


class MessageStorageMiddleware(BaseMiddleware):
    """
    Middleware to store incoming messages into a Redis queue for processing.
    """

    async def __call__(self, handler, event: Message, data: dict):
        """
        Hook called before processing each message.
        """
        if 'command' not in data:  
            event.bot.logger.info("Save message")
            try:
                # Enqueue message data to Celery
                save_message_task.delay(**event.dict())
            except Exception as e:
                event.bot.logger.error(f"Failed to enqueue message storage task: {e}")
            
        return await handler(event, data)


class UserFetchingMiddleware(BaseMiddleware):
    """
    Middleware to fetch or create a User object from the database
    based on the incoming message.
    """

    async def __call__(self, handler, event: Message, data: dict):
        """
        Hook called before processing each message to fetch or create the User object.
        """
        user_id = event.from_user.id if event.from_user else None

        if user_id:
            event.bot.logger.info(f"Fetching user {user_id} from the database or creating a new record.")
            try:
                # Fetch or create the user object
                user = get_user_or_create(**event.from_user.dict())
                # add to event orm user
                data['user'] = user
            except Exception as e:
                event.bot.logger.error(f"Failed to fetch or create user: {e}")
                data['user'] = None
        else:
            event.bot.logger.warning("Message does not have a user ID. Skipping user processing.")
            data['user'] = None

        return await handler(event, data)
    

class MessageCacheMiddleware(BaseMiddleware):
    """
    Middleware to store incoming messages into Redis for temporary caching
    and processing with Celery.
    """

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=3):
        super().__init__()
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    async def __call__(self, handler, event: Message, data: dict):
        """
        Hook called before processing each message.
        """
        if 'command' not in data:  # Skip commands
            event.bot.logger.info("Processing message for storage")
            try:
                user_id = event.from_user.id
                message_id = event.message_id
                timestamp = event.date.timestamp()
                cache_key = f"user:{user_id}:messages"

                # Append the message to the Redis cache
                event_str = json.dumps(event.dict(), indent=4, sort_keys=True, default=str)
                self.redis_client.rpush(cache_key, event_str)
                self.redis_client.expire(cache_key, 5)  # Set expiration for 3 seconds

                # Optionally, check for other parts of the message
                messages = self.redis_client.lrange(cache_key, 0, -1)
                if len(messages) > 1:  # Example check for multiple parts
                    return 
            except Exception as e:
                event.bot.logger.error(f"Failed to process and store message: {e}")

        return await handler(event, data)