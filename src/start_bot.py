import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import ErrorEvent

from tasks.messages import process_message
from bot import middleware, handlers, errors
from bot.handlers import FSMPrompt
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

# send billing
dp.message(Command("invoice"))(handlers.send_invoice_handler)
# Обработчик для подписки (пример уже существующего функционала)
dp.callback_query(lambda c: c.data == "donate")(handlers.donate_callback_handler)
# Обработчик для ввода суммы доната и отправки инвойса
dp.message(StateFilter(FSMPrompt.donating))(handlers.donation_amount_handler)
# Обработчик pre-checkout запроса (для всех платежей)
dp.pre_checkout_query()(handlers.process_pre_checkout_query)
# Обработчик успешного платежа (для всех платежей)
dp.message(lambda m: m.successful_payment is not None)(handlers.process_successful_payment)
# Обработчик неуспешного платежа (если требуется)
dp.message(StateFilter(FSMPrompt.buying))(handlers.process_unsuccessful_payment)

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