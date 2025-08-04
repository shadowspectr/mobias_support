# main_handlers.py (НОВЫЙ ФАЙЛ)
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from keyboard import get_start_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот магазина 'MobiAs'. Чем могу помочь?",
        reply_markup=get_start_keyboard()
    )

@router.message(F.text == "🏬 Адреса магазинов")
async def show_shop_addresses(message: types.Message):
    addresses = (
        "📍 <b>Г. Мелитополь, Пр-т Б. Хмельницкого 24</b>\n"
        "🏢 ТЦ Пассаж, вход 2\n"
        "⏰ С 9:00 до 17:00\n\n"
        "📍 <b>Г. Мелитополь, Пр-т Б. Хмельницкого 30</b>\n"
        "⏰ С 9:00 до 18:00\n\n"
        "📍 <b>Г. Мелитополь, ул. Кирова 94</b>\n"
        "🏢 ТЦ Люкс, 1-й этаж\n"
        "⏰ С 9:00 до 18:00"
    )
    await message.answer(addresses)

@router.message(F.text == "🎁 Актуальные акции")
async def handle_promotions(message: types.Message):
    await message.answer("В данный момент активных акций нет. Следите за обновлениями!")

@router.callback_query(F.data == "open_main")
async def process_open_main(callback: types.CallbackQuery):
    if callback.message.reply_markup:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()

# --- Fallback Handler ---
# Этот обработчик должен быть последним в этом роутере
@router.message()
async def fallback_handler(message: types.Message):
    logging.warning(f"Неизвестный запрос от {message.from_user.id}: {message.text}")
    await message.answer(
        "🤖 Я не совсем понял ваш запрос.\n\n"
        "Пожалуйста, воспользуйтесь кнопками в меню, чтобы выбрать нужный раздел.",
        reply_markup=get_start_keyboard()
    )