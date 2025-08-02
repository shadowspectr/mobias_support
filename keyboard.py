from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard():
    """Основная клавиатура с кнопками бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏬 Адреса магазинов"),
                KeyboardButton(text="🎁 Актуальные акции")
            ],
            [
                KeyboardButton(text="📍 Найти пункт выдачи поблизости")
            ],
            [
                KeyboardButton(text="📦 Как пользоваться доставкой?"),
                KeyboardButton(text="ℹ️ Как оплатить доставку?")
            ],
            [
                KeyboardButton(text="ℹ️ Как открыть свой пункт выдачи?")
            ],
            [
                KeyboardButton(text="❓ Обратиться в поддержку")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_support_inline_keyboard():
    """Инлайн клавиатура для поддержки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Задать вопрос", callback_data="support")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="open_main")]
    ])
    return keyboard

def get_back_to_main_keyboard():
    """Кнопка возврата в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="open_main")]
    ])
    return keyboard