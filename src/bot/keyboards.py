from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config


def get_models_keyboard():
    """
    Create an inline keyboard with model options.
    """
    inline_keyboard = []
    for model_name, model_info in config.model_config.items():
        if model_name == 'default':
            continue
        button = InlineKeyboardButton(
            text=f"{model_name}",
            title=f"{model_info['description']}",
            callback_data=f"model:{model_name}"
        )
        inline_keyboard.append([button])  # Each button in its own row

    # Pass the constructed inline_keyboard to InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)