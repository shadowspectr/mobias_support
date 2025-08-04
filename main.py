# main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv

# Локальные импорты
from keyboard import get_start_keyboard
from support_handler import router as support_router
from src.broadcast import send_random_ad # Предполагается, что этот модуль у вас есть
import keep_alive # Предполагается, что этот модуль у вас есть

# --- Загрузка окружения ---
load_dotenv()
BOT_TOKEN = os.getenv('API_KEY')
if not BOT_TOKEN:
    raise ValueError("Не найден API_KEY в .env файле")

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- Подключение роутеров ---
# Важно! Роутер поддержки должен идти первым, чтобы он перехватывал
# сообщения от пользователей в активных диалогах и состояниях FSM.
dp.include_router(support_router)


# --- Обработчики команд и кнопок главного меню ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот магазина 'MobiAs'. Чем могу помочь?",
        reply_markup=get_start_keyboard()
    )

@dp.message(F.text == "🏬 Адреса магазинов")
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

@dp.message(F.text == "🎁 Актуальные акции")
async def handle_promotions(message: types.Message):
    # Здесь можно разместить код для отправки акций
    # Для примера, используем ваш существующий метод
    # await send_random_ad(bot) # Если хотите всем
    # await send_ad_to_user(bot, message.from_user.id) # Если конкретному пользователю
    await message.answer("В данный момент активных акций нет. Следите за обновлениями!")

@dp.callback_query(F.data == "open_main")
async def process_open_main(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None) # Убираем инлайн кнопку
    await callback.message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()

# --- Fallback Handler (обработчик для всех остальных сообщений) ---
@dp.message()
async def fallback_handler(message: types.Message):
    # Этот обработчик сработает, если ни один другой обработчик
    # (включая те, что в support_router) не поймал сообщение.
    logging.warning(f"Неизвестный запрос от {message.from_user.id}: {message.text}")
    await message.answer(
        "🤖 Я не совсем понял ваш запрос.\n\n"
        "Пожалуйста, воспользуйтесь кнопками в меню, чтобы выбрать нужный раздел.",
        reply_markup=get_start_keyboard()
    )

# --- Функции запуска и остановки ---
async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот успешно запущен")

async def main():
    dp.startup.register(on_startup)
    try:
        if 'keep_alive' in globals():
            keep_alive.keep_alive()
            logging.info("Keep-alive сервер запущен.")
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())