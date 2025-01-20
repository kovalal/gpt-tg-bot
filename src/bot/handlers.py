from models import User
from aiogram import types

import tasks.messages
from .keyboards import get_models_keyboard
from dt import retrive, update
import tasks


async def clear_context_handler(message: types.Message, *args, user: User = None, bot=None, **kwargs):
    """
    Handler for clearing chat context.
    Removes forced reply markup from the bot's last message.
    """
    try:
        tg_msg = await bot.send_message(chat_id=user.id, text="Reply markup cleared", reply_markup=types.ReplyKeyboardRemove())
        await bot.delete_message(chat_id=user.id, message_id=tg_msg.message_id)
    except Exception as e:
        message.bot.logger.error(f"Failed to clear forced reply for user {user.id}: {repr(e)}")


async def model_command_handler(message: types.Message, *args, user: User = None, **kwargs):
    """
    Handler for the /model command.
    Shows the menu for model selection.
    """
    current_model = user.model or "gpt-4o-mini"

    await message.answer(f"Вы используете модель {current_model}. Выберите какую модель вы хотите использовать дальше:", 
                         reply_markup=get_models_keyboard())


async def model_callback_handler(callback_query: types.CallbackQuery):
    """
    Handle the selection of a model from the inline keyboard.
    Updates the user's model in the database.
    
    :param callback_query: CallbackQuery object
    :param session: SQLAlchemy session instance
    """
    model_name = callback_query.data.split(":")[1]

    # Retrieve the user from the database
    user_id = callback_query.from_user.id
    user = retrive.retrive_user(user_id)
    update.set_user_model(user, model_name)

    await callback_query.message.answer(f"Your model has been set to: {model_name}")
    await callback_query.answer()


async def prompt_handler(message: types.Message, *args, user=None, bot=None, **kwargs):
    try:
        # Enqueue message processing task
        clock_msg = await message.reply("⏳")
        task = tasks.messages.process_message.delay(clock_msg.message_id, **message.dict(), user=user.as_dict())
        bot.logger.info(f"Enqueued task: {task.id}")
    except Exception as e:
        bot.logger.error(f"Failed to enqueue task: {e}")
        await message.reply("При обработке сообщения произошла ошибка. Попробуйте позднее")
        raise