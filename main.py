# main.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from support_handler import router as support_router
from main_handlers import router as main_handlers_router
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
# ===== ВАЖНО: ПОРЯДОК ИЗМЕНЕН НА ПРАВИЛЬНЫЙ =====
# Сначала регистрируем роутер с главными кнопками.
# Он будет иметь приоритет и сможет "перехватывать" нажатия кнопок у пользователей в любом состоянии.
dp.include_router(main_handlers_router)

# Роутер поддержки идет вторым. Его обработчик состояния сработает только если
# сообщение не подошло ни под один из фильтров в main_handlers_router.
dp.include_router(support_router)

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