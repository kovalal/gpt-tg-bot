from models import User
from aiogram import types
from aiogram.fsm.context import FSMContext

import tasks.messages
from .keyboards import get_models_keyboard
from dt import retrive, update, create
import tasks
import config
import json


async def start(message: types.Message, *args, user=None, bot=None, **kwargs):
    await message.answer(
        "Пиши свой запрос.\n" 
        "Поддерживаемые модели: gpt-4o-mini, gpt-4o, o1, dallee.\n"
        "Если хочешь, чтобы твой запрос обработала конкретная модель, попроси об этом в сообщении.",
        parse_mode="HTML"
    )

class FSMPrompt:
    buying = "buying"
    donating = "donating"
    

# Обработчик команды для отправки инвойса
async def send_invoice_handler(message: types.Message, *args, user=None, bot=None, **kwargs):
    try:
        # Логирование начала процесса
        bot.logger.info(f"Processing payment for user: {user.id if user else 'Unknown'}")

        # Создание сообщения с кнопкой
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            #[
            #    types.InlineKeyboardButton(
            #        text="Месячная подписка - 300",
            #        callback_data="subscribe_month"
            #    )
            #],
            [
                types.InlineKeyboardButton(
                    text="Донатить",
                    callback_data="donate"
                )
            ]
        ])

        await message.answer(
            #"<b>Оплата подписки</b>\n\n"
            #"При оплате вы получаете возможность пользоваться ботом в течении месяца.\n"
            #"Пожалуйста, выберите удобный метод оплаты:",
            "<b>Финансовая поддержка проекта</b>\n\n",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        # Логирование ошибок
        bot.logger.error(f"Failed to process payment: {e}")
        await message.reply("Произошла ошибка при создании платежа. Попробуйте снова.")
        raise


# Обработчик для кнопки "Донатить"
async def donate_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    # Запрос у пользователя ввода суммы доната в рублях
    await callback_query.message.answer("Введите сумму доната в рублях (например, введите 100 для 100 рублей):")
    # Устанавливаем состояние для ожидания ввода суммы
    await state.set_state(FSMPrompt.donating)
    await callback_query.answer()

# Обработчик для ввода суммы доната и отправки инвойса
async def donation_amount_handler(message: types.Message, state: FSMContext):
    try:
        amount_text = message.text.strip()
        if not amount_text.isdigit():
            await message.reply("Пожалуйста, введите сумму в рублях, используя только цифры не менее 100 (например, 500).")
            return
        # Конвертируем рубли в копейки
        rubles = int(amount_text)
        donation_amount = rubles * 100
        prices = [types.LabeledPrice(label="Донат", amount=donation_amount)]
        
        await message.answer_invoice(
            title="Донат",
            description="Благодарим за вашу поддержку!",
            payload="donation_payload",
            provider_token=config.PROVIDER_TOKEN,
            currency='RUB',
            prices=prices,
            need_phone_number=False,
            need_email=False
        )
        await state.clear()
    except Exception as e:
        message.bot.logger.error(f"Ошибка при обработке доната: {e}")
        await message.reply("Произошла ошибка при обработке вашего доната. Попробуйте еще раз.")
        await state.clear()


# Обработчик pre-checkout запроса (для всех платежей)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обработчик успешного платежа (для всех платежей)
# Если хотите отлавливать по фильтру успешного платежа, можно использовать F.successful_payment
async def process_successful_payment(message: types.Message, state: FSMContext):
    try:
        # Извлекаем информацию об успешном платеже из сообщения
        sp = message.successful_payment
        total_amount = sp.total_amount  # сумма в копейках
        rubles = total_amount // 100      # переводим в рубли
        currency = sp.currency
        payload = sp.invoice_payload

        # Сохраняем информацию о платеже в базе данных
        create.create_payment(message)

        # Обработка в зависимости от типа платежа
        if payload == "donation_payload":
            await message.reply(f"Спасибо за донат на сумму {rubles} {currency}!🙏")
            # Здесь можно добавить дополнительную логику для обработки доната (например, обновление БД)
        elif payload == "bot_paid":
            await message.reply(f"Платеж за подписку на сумму {rubles} {currency} прошел успешно!")
            # Здесь можно добавить логику для обработки подписки (например, выдача доступа)
        else:
            await message.reply(f"Платеж на сумму {rubles} {currency} прошел успешно!")

    except Exception as e:
        message.bot.logger.error(f"Ошибка при обработке успешного платежа: {e}")
    finally:
        # Очистка состояния, если оно установлено
        current_state = await state.get_state()
        if current_state is not None:
            await state.clear()

# Обработчик неуспешного платежа (если требуется)
async def process_unsuccessful_payment(message: types.Message, state: FSMContext):
    await message.reply("Не удалось выполнить платеж!")
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()


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
    current_model = user.model or "auto"

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
        task = tasks.messages.process_message.delay(clock_msg_id=clock_msg.message_id, **message.dict(), user=user.as_dict())
        bot.logger.info(f"Enqueued task: {task.id}")
    except Exception as e:
        bot.logger.error(f"Failed to enqueue task: {e}")
        await message.reply("При обработке сообщения произошла ошибка. Попробуйте позднее")
        raise


async def voice_handler(message: types.Message, *args, user=None, bot=None, **kwargs):
    # ставим выполнение транскрибации в очередь
    try:
        # Enqueue message processing task
        print(message)
        clock_msg = await message.reply("⏳")
        task = tasks.messages.transcribe_voice.delay(clock_msg_id=clock_msg.message_id, message=message.dict(), user=user.as_dict())
        bot.logger.info(f"Enqueued task: {task.id}")
    except Exception as e:
        bot.logger.error(f"Failed to enqueue task: {e}")
        await message.reply("При обработке сообщения произошла ошибка. Попробуйте позднее")
        raise


async def notify_handler(message: types.Message, *args, user=None, bot=None, **kwargs):
    """
    Обрабатывает команду /notify. Текст уведомления должен быть передан сразу после команды.
    Например: /notify Внимание! Обновление системы.
    
    :param message: входящее сообщение
    :param db: экземпляр сессии SQLAlchemy (или асинхронная сессия), через которую можно выполнить запрос
    """
    # Извлекаем текст уведомления (все, что после /notify)
    notify_text = message.text.lstrip('/notify')
    if not notify_text:
        await message.reply("Пожалуйста, укажите текст уведомления после команды /notify")
        return
    
    # Получаем всех пользователей из базы
    users = retrive.retrive_all_users()
    sent_count = 0
    for user in users:
        try:
            # Отправляем уведомление каждому пользователю
            await message.bot.send_message(user.id, notify_text)
            sent_count += 1
        except Exception as e:
            message.bot.logger.error(f"Ошибка отправки уведомления пользователю {user.id}: {e}")

    await message.reply(f"Уведомление отправлено {sent_count} пользователям.")