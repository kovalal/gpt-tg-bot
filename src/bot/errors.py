from aiogram import Bot
from aiogram.types import ErrorEvent
from functools import wraps
import traceback
import config


bot = Bot(config.BOT_TOKEN)

async def error_handler(event: ErrorEvent, bot: Bot = None) -> None :
    chat = event.update.message.chat
    error_msg = f'Ошибка ({chat.id}) {chat.username} {chat.last_name} {chat.first_name} - {event.exception}'\
    f'\nСообщение - {event.update.message.text}'
    await bot.send_message(config.ERROR_CHAT_ID, error_msg)


def send_error(coro):
    @wraps(coro)
    async def wrapped(*args, user=None, **kwargs):
        try:
            return await coro(*args, user=user, **kwargs)
        except Exception as e:
            error_msg = f"Ошибка ({user['id']}) {user['username']} {user['last_name']} {user['first_name']} - {e}"\
            f"\n{traceback.format_exc(-1)}"
            await bot.send_message(config.ERROR_CHAT_ID, error_msg)
            raise
    return wrapped
