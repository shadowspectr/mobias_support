import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, Message
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramAPIError
from dotenv import load_dotenv
from keyboard import get_start_keyboard
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardRemove
from callback_handler import callback_router
import pandas as pd
from geopy.distance import geodesic
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keep_alive
from support_handler import callback_router as support_router
from partner_handler import partner_router


load_dotenv()

BOT_TOKEN = os.getenv('API_KEY')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(partner_router)
dp.include_router(callback_router)
dp.include_router(support_router)
df = pd.read_excel('map.xlsx')
router = Router()

# ID чата техподдержки (замените на реальный)
SUPPORT_CHAT_ID =-1002837608854


# Состояния для FSM
class SupportState(StatesGroup):
    waiting_for_question = State()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Обновляем интерфейс...", reply_markup=ReplyKeyboardRemove())
    await message.answer("Привет - привет 👋 "
                         "Ваш запрос уже у нас 💬"
                         "<b>Очень скоро</b> с вами свяжется наш специалист!",
                         reply_markup=get_start_keyboard(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "open_main")
async def process_open_main(callback: types.CallbackQuery):
    await callback.answer()  # Отвечаем на callback, чтобы убрать "часики" у кнопки
    await callback.message.answer("Обновляем интерфейс...", reply_markup=ReplyKeyboardRemove())
    await callback.message.answer(
        "Приветствую! Я бот +7Доставки. Расскажу, как бесплатно получать товары с "
        "<a href='https://www.ozon.ru/'>топового маркетплейса РФ</a>.",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML"
    )


# Callback для вызова техподдержки
@dp.callback_query(lambda c: c.data == "support")
async def support_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🛠 Пожалуйста, опишите вашу проблему или задайте вопрос.")
    await state.set_state(SupportState.waiting_for_question)  # Устанавливаем состояние ожидания вопроса


# Обработка вопроса от пользователя
@dp.message(SupportState.waiting_for_question)
async def handle_question(message: types.Message, state: FSMContext, bot: Bot):
    user_question = message.text

    # Пересылаем вопрос в чат техподдержки
    forward_message = await bot.send_message(
        SUPPORT_CHAT_ID,
        f"🔔 Вопрос от пользователя @{message.from_user.username} (ID: {message.from_user.id}):\n{user_question}"
    )

    # Сохраняем данные для ответа
    await state.update_data(user_chat_id=message.chat.id, support_message_id=forward_message.message_id)

    await message.answer("✅ Ваш вопрос отправлен в службу поддержки. Ожидайте ответа.")
    await state.clear()  # Очищаем состояние


# Обработка ответа от техподдержки
@dp.message(F.chat.id == SUPPORT_CHAT_ID)
async def forward_answer_from_support(message: types.Message, bot: Bot):
    if message.reply_to_message:
        # Извлекаем ID пользователя
        question_info = message.reply_to_message.text.split('\n')[0]
        user_id = int(question_info.split('(ID: ')[1].replace('):', ''))

        # Пересылаем ответ пользователю
        await bot.send_message(
            user_id,
            f"💬 Ответ от службы поддержки:\n{message.text}"
        )


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
            # Добавляем флаг приоритетности
            is_priority = row['адрес'] == priority_location
            nearby_locations.append((row['адрес'], distance, row['ссылка'], row['широта'], row['долгота'], is_priority))

    # Сортируем с приоритетным местоположением первым
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



dp.include_router(router)


# Функция запуска бота
async def main():
    # Удаляем вебхук перед запуском бота
    await delete_webhook()
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except TelegramAPIError as e:
        logging.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    keep_alive.keep_alive()
    asyncio.run(main())
