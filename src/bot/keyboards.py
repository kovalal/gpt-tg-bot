from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config


def get_models_keyboard():
    """
    Create an inline keyboard with model options.
    """
    inline_keyboard = [
        [InlineKeyboardButton(
            text="auto",
            title="Бот сам выберет подходящую Вам модель",
            callback_data="model:auto"
        )]
    ]
    for model_name, model_info in config.model_config.items():
        if model_info.get("menu") is None:
            continue
        button = InlineKeyboardButton(
            text=f"{model_name}",
            title=f"{model_info['description']}",
            callback_data=f"model:{model_name}"
        )
        inline_keyboard.append([button])  # Each button in its own row
    # Pass the constructed inline_keyboard to InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# Функция для создания клавиатуры настроек
def get_settings_keyboard():
    buttons = []
    # Кнопка для выбора модели
    model_button = InlineKeyboardButton(text="Модель", callback_data="settings:model")
    retain_context_button = InlineKeyboardButton(
        text="Автоматическое удержание контекста", 
        callback_data="settings:retain_context"
    )
    buttons.append([model_button])
    buttons.append([retain_context_button])
    # Здесь можно добавить и другие кнопки настроек, если потребуется
    return InlineKeyboardMarkup(inline_keyboard=buttons)