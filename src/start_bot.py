import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ErrorEvent

from tasks.messages import process_message
from bot import middleware, handlers, errors
import models
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gptBot')

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
bot.logger = logger

# dispatcher
dp = Dispatcher()
# middlewares
# get user middleware
dp.message.middleware(middleware.UserFetchingMiddleware())
# store message middleware
dp.message.middleware(middleware.MessageStorageMiddleware())
# cache user`s message
dp.message.middleware(middleware.MessageCacheMiddleware())

# handlers
# model menu handler
dp.message(Command("model"))(handlers.model_command_handler)
dp.callback_query(lambda callback: callback.data.startswith("model:"))(handlers.model_callback_handler)
# clear context handler
dp.message(Command("clear"))(handlers.clear_context_handler)
# handler for prompt
dp.message()(handlers.prompt_handler)
# add error handler
@dp.errors(errors.error_handler)


async def main() -> None:
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped")