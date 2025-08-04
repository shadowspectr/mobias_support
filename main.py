# main.py (ФИНАЛЬНАЯ ВЕРСИЯ)
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from support_handler import router as support_router, SUPPORT_TICKETS_CHAT_ID
from main_handlers import router as main_handlers_router
from keyboard import get_start_keyboard
import keep_alive

# --- Загрузка и конфигурация ---
load_dotenv()
BOT_TOKEN = os.getenv('API_KEY')
if not BOT_TOKEN:
    raise ValueError("Не найден API_KEY в .env файле")

logging.basicConfig(level=logging.INFO)

# --- Инициализация ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- РЕГИСТРАЦИЯ РОУТЕРОВ ---
# Регистрируем роутеры с КОНКРЕТНЫМИ командами и кнопками.
# Порядок этих двух роутеров теперь не так критичен, но так логичнее.
dp.include_router(main_handlers_router)
dp.include_router(support_router)

# --- ОБРАБОТЧИК ПО УМОЛЧАНИЮ (FALLBACK) ---
# Этот обработчик регистрируется ПОСЛЕДНИМ и напрямую в диспетчере.
# Он сработает, только если сообщение не было поймано ни в одном из роутеров выше.
@dp.message()
async def fallback_handler(message: types.Message):
    # Игнорируем сообщения в чате поддержки
    if message.chat.id == SUPPORT_TICKETS_CHAT_ID:
        return
        
    logging.warning(f"Неизвестный запрос от {message.from_user.id}: {message.text or '[нетекстовое сообщение]'}")
    await message.answer(
        "🤖 Я не совсем понял ваш запрос.\n\n"
        "Пожалуйста, воспользуйтесь кнопками в меню.\n"
        "Если вы хотите задать вопрос нашей поддержке, нажмите кнопку '❓ Задать вопрос'.",
        reply_markup=get_start_keyboard()
    )


# --- Функции запуска ---
async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот успешно запущен")

async def main():
    dp.startup.register(on_startup)
    try:
        if 'keep_alive' in globals():
            keep_alive.keep_alive()
        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())