import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, Message
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramAPIError
from dotenv import load_dotenv
from keyboard import get_start_keyboard
from aiogram.types import ReplyKeyboardRemove
from callback_handler import callback_router
from middlewares.log_user import UserLoggingMiddleware
import pandas as pd
from geopy.distance import geodesic
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keep_alive
from support_handler import callback_router as support_router
from partner_handler import partner_router
from src.broadcast import send_random_ad
from src.broadcast import send_ad_to_user

load_dotenv()

BOT_TOKEN = os.getenv('API_KEY')
USER_IDS_FILE = "user_ids.txt"

def load_user_ids():
    try:
        if not os.path.exists(USER_IDS_FILE):
            with open(USER_IDS_FILE, "w") as f:
                pass
            logging.info("Создан новый файл user_ids.txt")
            return set()
        with open(USER_IDS_FILE, "r") as file:
            return set(line.strip() for line in file if line.strip().isdigit())
    except Exception as e:
        logging.error(f"Ошибка при загрузке user_ids.txt: {e}")
        return set()

def save_user_id(user_id: int):
    try:
        user_ids = load_user_ids()
        if str(user_id) not in user_ids:
            with open(USER_IDS_FILE, "a") as file:
                file.write(f"{user_id}\n")
            logging.info(f"Добавлен новый user_id: {user_id}")
        else:
            logging.info(f"user_id {user_id} уже в списке")
    except Exception as e:
        logging.error(f"Ошибка при сохранении user_id {user_id}: {e}")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.middleware(UserLoggingMiddleware())
dp.callback_query.middleware(UserLoggingMiddleware())
dp.include_router(partner_router)
dp.include_router(callback_router)
dp.include_router(support_router)  # Роутер поддержки должен быть включен
df = pd.read_excel('map.xlsx')
router = Router()

# ID чата для тикетов (группа, не диалог)
SUPPORT_TICKETS_CHAT_ID = -4961897884

KNOWN_BUTTON_TEXTS = {
    "📦 Как пользоваться доставкой?",
    "ℹ️ Как оплатить доставку?", 
    "ℹ️ Как открыть свой пункт выдачи?",
    "📍 Найти пункт выдачи поблизости",
    "❓ Обратиться в поддержку",
    "🏬 Адреса магазинов",
    "🎁 Актуальные акции"
}

# Убираем состояния поддержки - они теперь в support_handler.py

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user_id(message.from_user.id)  # Сохраняем ID пользователя
    await message.answer("Обновляем интерфейс...", reply_markup=ReplyKeyboardRemove())
    await message.answer("Привет - привет 👋 \n"
                         "Я бот магазина цифровой продукции 'MobiAs'! \n"
                         "Задавай свои вопросы, мы всегда будем рады помочь!",
                         reply_markup=get_start_keyboard(), parse_mode="HTML")

@dp.message(Command("list"))
async def list_user_ids(message: types.Message):
    user_ids = load_user_ids()
    if not user_ids:
        await message.answer("Список пользователей пуст.")
    else:
        await message.answer("Список ID пользователей:\n" + "\n".join(user_ids))

@dp.message(Command("broadcast"))
async def broadcast_ads(message: types.Message):
    await message.answer("Рассылаю рекламу...")
    await send_random_ad(bot)

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
    await message.answer(addresses, parse_mode="HTML")

@dp.message(F.text == "🎁 Актуальные акции")
async def handle_promotions(message: types.Message, bot: Bot):
    await send_ad_to_user(bot, message.from_user.id)

@dp.callback_query(lambda c: c.data == "open_main")
async def process_open_main(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Обновляем интерфейс...", reply_markup=ReplyKeyboardRemove())
    await callback.message.answer(
        "Приветствую! Я бот +7Доставки. Расскажу, как бесплатно получать товары с "
        "<a href='https://www.ozon.ru/'>топового маркетплейса РФ</a>.",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )

# Обработчик для кнопки "Обратиться в поддержку" - теперь в support_handler.py

# Функция для удаления вебхука
async def delete_webhook():
    try:
        await bot.delete_webhook()
        logging.info("Вебхук успешно удален")
    except TelegramAPIError as e:
        logging.error(f"Ошибка при удалении вебхука: {e}")

# Функция поиска ближайших пунктов
def get_nearby_locations(user_location, max_distance_km=2):
    nearby_locations = []
    priority_location = "Донецк, пл. Конституции, д.4"

    for index, row in df.iterrows():
        location = (row['широта'], row['долгота'])
        distance = geodesic(user_location, location).kilometers
        if distance <= max_distance_km:
            is_priority = row['адрес'] == priority_location
            nearby_locations.append((row['адрес'], distance, row['ссылка'], row['широта'], row['долгота'], is_priority))

    return sorted(nearby_locations, key=lambda x: (not x[5], x[1]))

@dp.message(F.content_type == ContentType.LOCATION)
async def handle_location(message: Message):
    logging.info(f"Получена геопозиция: {message.location.latitude}, {message.location.longitude}")
    user_location = (message.location.latitude, message.location.longitude)
    nearby_locations = get_nearby_locations(user_location)

    if nearby_locations:
        response = "<b>Вот ближайшие к вам пункты выдачи:</b>\n\n"
        for address, distance, link, lat, lon, is_priority in nearby_locations:
            yandex_maps_url = f"https://yandex.ru/maps/?ll={lon},{lat}&z=16&mode=search&text={address}"
            response += f"📍 <b>{address}</b> - {distance:.2f} км\n"
            response += f"🔗 <a href='{link}'>Добавить пункт выдачи в Ozon</a>\n"
            response += f"🗺️ <a href='{yandex_maps_url}'>Открыть в Яндекс.Картах</a>\n\n"
    else:
        response = "К сожалению, в радиусе 2 км нет точек."

    await message.reply(response, parse_mode="HTML")

# Fallback обработчик для неизвестных сообщений (только приватные чаты)
@dp.message(lambda message: (
    message.chat.id != SUPPORT_TICKETS_CHAT_ID and 
    message.chat.type == "private" and
    message.from_user.id not in [info.get('support_user_id') for info in getattr(support_router, 'active_dialogs', {}).values()]
))
async def fallback_handler(message: types.Message, bot: Bot):
    # Если текст совпадает с известными кнопками — не обрабатываем
    if message.text and message.text.strip() in KNOWN_BUTTON_TEXTS:
        return

    # Направляем к боту для получения помощи
    await message.answer(
        "🤖 Я не понял ваш запрос.\n\n"
        "Для получения помощи воспользуйтесь кнопкой '❓ Обратиться в поддержку' или выберите нужный раздел из меню.",
        reply_markup=get_start_keyboard()
    )

dp.include_router(router)

# Функция запуска бота
async def main():
    await delete_webhook()
    try:
        await dp.start_polling(bot)
    except TelegramAPIError as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    keep_alive.keep_alive()
    asyncio.run(main())