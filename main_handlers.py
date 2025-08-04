# main_handlers.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import logging
import json
import os
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.types import FSInputFile
from keyboard import get_start_keyboard
# Импортируем тексты кнопок из констант
from constants import ADDRESS_BUTTON_TEXT, PROMOTION_BUTTON_TEXT

router = Router()

# --- Константы для папки с акциями ---
ADS_DIR = "ads"
PROMOTIONS_FILE = os.path.join(ADS_DIR, "promotions.json")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот магазина 'MobiAs'. Чем могу помочь?",
        reply_markup=get_start_keyboard()
    )

@router.message(F.text == ADDRESS_BUTTON_TEXT)
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

@router.message(F.text == PROMOTION_BUTTON_TEXT)
async def handle_promotions(message: types.Message, bot: Bot):
    # ... код обработчика акций без изменений ...
    try:
        if not os.path.exists(PROMOTIONS_FILE):
            await message.answer("К сожалению, сейчас нет доступных акций. Загляните позже!")
            return
        with open(PROMOTIONS_FILE, "r", encoding="utf-8") as f:
            ads_data = json.load(f)
        if not ads_data:
            await message.answer("В данный момент активных акций нет. Следите за обновлениями!")
            return
        for ad in ads_data:
            text = ad.get("text", "")
            image_path = os.path.join(ADS_DIR, ad.get("image", ""))
            if os.path.exists(image_path):
                await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(image_path), caption=text)
            else:
                await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка при отправке акций: {e}")
        await message.answer("Произошла ошибка при загрузке акций.")

@router.callback_query(F.data == "open_main")
async def process_open_main(callback: types.CallbackQuery):
    if callback.message.reply_markup:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Вы вернулись в главное меню.", reply_markup=get_start_keyboard())
    await callback.answer()

# ===== ОБРАБОТЧИК ПО УМОЛЧАНИЮ ОТСЮДА УДАЛЕН! =====