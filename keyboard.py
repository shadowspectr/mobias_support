# keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard():
    """Возвращает основную клавиатуру с шорткатами."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏬 Адреса магазинов")],
            [KeyboardButton(text="🎁 Актуальные акции")],
            [KeyboardButton(text="❓ Задать вопрос")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )
    return keyboard

def get_back_to_menu_keyboard():
    """Возвращает инлайн-клавиатуру для возврата в главное меню."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="open_main")]
    ])
    return keyboard