# main_handlers.py (ФИНАЛЬНАЯ ВЕРСИЯ)
import logging
import json
import os
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.types import FSInputFile
from keyboard import get_start_keyboard
from support_handler import SUPPORT_TICKETS_CHAT_ID
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

# --- Обработчик для кнопки "Актуальные акции" ---
@router.message(F.text == PROMOTION_BUTTON_TEXT)
async def handle_promotions(message: types.Message, bot: Bot):
    try:
        # Проверяем, существует ли файл с акциями
        if not os.path.exists(PROMOTIONS_FILE):
            logging.warning(f"Файл с акциями не найден: {PROMOTIONS_FILE}")
            await message.answer("К сожалению, сейчас нет доступных акций. Загляните позже!")
            return

        with open(PROMOTIONS_FILE, "r", encoding="utf-8") as f:
            ads_data = json.load(f)

        if not ads_data:
            await message.answer("В данный момент активных акций нет. Следите за обновлениями!")
            return
        
        # Отправляем каждую акцию отдельным сообщением
        for ad in ads_data:
            text = ad.get("text", "Описание акции отсутствует.")
            image_filename = ad.get("image")
            
            if image_filename:
                image_path = os.path.join(ADS_DIR, image_filename)
                if os.path.exists(image_path):
                    photo = FSInputFile(image_path)
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=photo,
                        caption=text
                    )
                else:
                    logging.error(f"Файл изображения для акции не найден: {image_path}")
                    await message.answer(text) # Отправляем только текст, если картинка потерялась
            else:
                # Если в JSON нет ключа "image", отправляем только текст
                await message.answer(text)

    except json.JSONDecodeError:
        logging.error(f"Ошибка декодирования JSON в файле: {PROMOTIONS_FILE}")
        await message.answer("Не удалось загрузить информацию об акциях. Попробуйте позже.")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при отправке акций: {e}")
        await message.answer("Произошла ошибка при загрузке акций. Мы уже работаем над этим.")


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
@router.message(lambda message: message.chat.id != SUPPORT_TICKETS_CHAT_ID)
async def fallback_handler(message: types.Message):
    logging.warning(f"Неизвестный запрос от {message.from_user.id}: {message.text or '[нетекстовое сообщение]'}")
    await message.answer(
        "🤖 Я не совсем понял ваш запрос.\n\n"
        "Пожалуйста, воспользуйтесь кнопками в меню.\n"
        "Если вы хотите задать вопрос нашей поддержке, нажмите кнопку '❓ Задать вопрос'.",
        reply_markup=get_start_keyboard()
    )