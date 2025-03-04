from tools import format_and_split_message_for_telegram
from aiogram.enums.parse_mode import ParseMode
from aiogram import types
import aiohttp
import functools
import io
import base64


def send_to_file(func):
    @functools.wraps(func)
    async def wrapper(bot, chat_id, message_id, text, clock_msg_id=None):
        try:
            return await func(bot, chat_id, message_id, text, clock_msg_id=None)
        except:
            error_file = types.BufferedInputFile(text.encode(), filename=f"{text[:20]}.txt")

            # Отправка файла пользователю
            sent_message = await bot.send_document(chat_id=chat_id, document=error_file, caption="Ошибка при отправке сообщения.")
        return sent_message
    return wrapper


@send_to_file
async def send_response(bot, chat_id, message_id, text, clock_msg_id=None):
    """
    Send response 
    """
    msgs = format_and_split_message_for_telegram(text)
    sent_messages = []  # To store the message objects

    if clock_msg_id:
        await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)

    # Send each message in the list
    for msg in msgs:
        try:
            sent_message = await bot.send_message1(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message_id,
                reply_markup=types.ForceReply() if msg == msgs[-1] else None  # ForceReply only for the last message
            )
        except Exception as e:
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=msg,
                reply_to_message_id=message_id,
                reply_markup=types.ForceReply() if msg == msgs[-1] else None  # ForceReply only for the last message
            )
        sent_messages.append(sent_message)
    return sent_messages


async def send_image_response(bot, chat_id, message_id, image_url, clock_msg_id=None, caption=None):
    """
    Send an image from a URL to a user.
    
    :param bot: Telegram bot instance.
    :param chat_id: ID of the chat to send the image to.
    :param message_id: ID of the message to reply to.
    :param image_url: URL of the image to send.
    :param caption: Optional caption for the image.
    """
    try:
        # Fetch the image from the URL
        if clock_msg_id:
            await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)


        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    # Read image content
                    image_data = await response.read()
                    
                    input_file = types.BufferedInputFile(image_data, filename="image.jpg")
                    # Send the image to the user
                    sent_message = await bot.send_photo(
                        chat_id=chat_id,
                        photo=input_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=message_id
                    )
                    return [sent_message]
                else:
                    raise Exception(f"Failed to fetch image. Status code: {response.status}")
    except Exception as e:
        # Handle any exceptions that occur during the process
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Failed to send the image. Error: {str(e)}",
            reply_to_message_id=message_id
        )


async def send_audio_response(bot, chat_id, message_id, audio_base64, transcript=None, clock_msg_id=None):
    """
    Send an audio response to a user.

    :param bot: Telegram bot instance.
    :param chat_id: ID of the chat to send the audio to.
    :param message_id: ID of the message to reply to.
    :param audio_base64: Base64-encoded audio data.
    :param transcript: Optional transcript of the audio.
    :param clock_msg_id: ID of the clock message to delete (if exists).
    """
    try:
        #if clock_msg_id:
        #    await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)

        # Декодируем аудиофайл из base64
        audio_data = base64.b64decode(audio_base64)

        # Создаем объект файла в памяти
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.ogg"  # Telegram лучше принимает OGG формат

        # Отправляем аудиофайл пользователю
        sent_message = await bot.send_voice(
            chat_id=chat_id,
            voice=types.BufferedInputFile(audio_file.getvalue(), filename="audio.ogg"),
            caption=transcript or "Аудиосообщение",
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=message_id
        )

        return [sent_message]

    except Exception as e:
        # Обработка ошибок
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Не удалось отправить аудиосообщение. Ошибка: {str(e)}",
            reply_to_message_id=message_id
        )


def delete_notify_decorator(bot):
    def decorator(task):
        @functools.wraps(task)
        async def wrapped(clock_msg_id=None, from_user=None, *args, **kwargs):
            try:
                result = await task(*args, from_user=from_user, **kwargs)
            except:
                raise
            finally:
                if clock_msg_id and from_user:
                    chat_id = from_user['id']
                    await bot.delete_message(chat_id=chat_id, message_id=clock_msg_id)
            return result
        return wrapped
    return decorator
        