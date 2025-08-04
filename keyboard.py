# keyboard.py (ОБНОВЛЕННАЯ ВЕРСИЯ)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from constants import PROMOTION_BUTTON_TEXT, ADDRESS_BUTTON_TEXT, SUPPORT_BUTTON_TEXT

def get_start_keyboard():
    """Возвращает основную клавиатуру с шорткатами."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADDRESS_BUTTON_TEXT)],
            [KeyboardButton(text=PROMOTION_BUTTON_TEXT)],
            [KeyboardButton(text=SUPPORT_BUTTON_TEXT)]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )
    return keyboard

def get_end_dialog_keyboard():
    """Возвращает клавиатуру с кнопкой завершения диалога."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=END_DIALOG_BUTTON_TEXT)]
        ],
        resize_keyboard=True
    )
    return keyboard
def get_back_to_menu_keyboard():
    """Возвращает инлайн-клавиатуру для возврата в главное меню."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="open_main")]
    ])
    return keyboard