from aiogram import Router, types
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import requests
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
import re

# ID чата для получения заявок
PARTNER_CHAT_ID =-1002837608854  # Замените на реальный ID
LOGGING_CHAT_ID = 521620770  # Новый ID для логирования
YANDEX_API_KEY = "7df099aa-c180-4c44-b0cd-258a05bdc8f2"
# Создаем роутер для обработки заявок партнёров
partner_router = Router()

region_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ДНР", callback_data="region_dnr")],
    [InlineKeyboardButton(text="ЛНР", callback_data="region_lnr")],
    [InlineKeyboardButton(text="Херсонская область", callback_data="region_kherson")],
    [InlineKeyboardButton(text="Запорожская область", callback_data="region_zaporozh")],
])

# Клавиатура для пропуска отправки фото
skip_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_photos")]
    ]
)

# Состояния для FSM
class PartnerApplicationState(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_region = State()
    waiting_for_address = State()
    waiting_for_photos = State()

# Клавиатура для кнопки подачи заявки
def get_partner_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Подать заявку", callback_data="submit_application")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Обработчик кнопки "Как стать партнером?"
@partner_router.callback_query(lambda c: c.data == "partner_info")
async def partner_info(callback: types.CallbackQuery):
    info_text = (
        "Компания +7Доставка активно развивает партнерскую сеть Пунктов выдачи заказов на новых территориях и в Крыму.\n\n"
        "Мы готовы рассмотреть Вас как потенциального партнера, если:\n"
        "- У вас есть помещение с большой проходимостью\n"
        "- Вы готовы применить наш брендбук для большей узнаваемости в городе\n"
        "- Имеете представление о работе Пункта Выдачи\n"
        "- Есть желание повышать узнаваемость совместно с нами\n\n"
        "Наши минимальные требования:\n"
        "- Площадь помещения от 30 кв. м\n"
        "- Первый этаж, удобный заход\n"
        "- Наличие рабочего места с ПК, интернета, стеллажей для склада посылок\n"
        "- Аккуратность в работе\n"
        "- Содержание пункта выдачи в чистоте и порядке\n\n"
        "Если вы подходите, нажмите на кнопку \"Подать заявку\" ниже."
    )
    await callback.message.answer(info_text, reply_markup=get_partner_keyboard(), parse_mode="HTML")

    # Логирование на случай, если кто-то нажал на кнопку партнерки
    logging.info(f"User {callback.from_user.id} clicked on the 'Как стать партнером?' button.")
    await callback.bot.send_message(LOGGING_CHAT_ID,f"User {callback.from_user.id} clicked on the 'Как стать партнером?' button.")

# Функция поиска адреса через Яндекс.Карты
def find_address_on_yandex(address):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": YANDEX_API_KEY, "geocode": address, "format": "json"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            geo_object = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            address_found = geo_object['metaDataProperty']['GeocoderMetaData']['text']
            coordinates = geo_object['Point']['pos']
            lon, lat = coordinates.split()
            map_link = f"https://yandex.ru/maps/?ll={lon},{lat}&z=16"
            return address_found, map_link
        except (IndexError, KeyError):
            return None, None
    return None, None

# Старт подачи заявки
@partner_router.callback_query(F.data == "submit_application")
async def start_application(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Пожалуйста, укажите ваше ФИО.")
    await state.set_state(PartnerApplicationState.waiting_for_full_name)

# Получение ФИО
@partner_router.message(StateFilter(PartnerApplicationState.waiting_for_full_name))
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Спасибо! Теперь укажите ваш номер телефона.")
    await state.set_state(PartnerApplicationState.waiting_for_phone)

# Получение телефона
@partner_router.message(StateFilter(PartnerApplicationState.waiting_for_phone))
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Выберите ваш регион:", reply_markup=region_keyboard)
    await state.set_state(PartnerApplicationState.waiting_for_region)

# Обработка выбора региона
@partner_router.callback_query(StateFilter(PartnerApplicationState.waiting_for_region))
async def get_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.split("_")[1]
    await state.update_data(region=region)
    await callback.message.answer("Спасибо! Укажите адрес вашего помещения.")
    await state.set_state(PartnerApplicationState.waiting_for_address)

# Получение адреса
@partner_router.message(StateFilter(PartnerApplicationState.waiting_for_address))
async def get_address(message: Message, state: FSMContext):
    user_data = await state.get_data()
    full_address = f"{user_data.get('region', '')}, {message.text}"

    address_found, map_link = find_address_on_yandex(full_address)
    if address_found:
        await state.update_data(address=message.text, address_found=address_found, map_link=map_link)
    else:
        await state.update_data(address=message.text, address_found="Адрес не найден", map_link="Нет данных")

    await message.answer(
        "Почти готово! Пожалуйста, отправьте фото или видео помещения (включая фасад). Если их нет, нажмите кнопку 'Пропустить'.",
        reply_markup=skip_keyboard
    )
    await state.set_state(PartnerApplicationState.waiting_for_photos)

# Обработка фото/видео и отправка заявки
# Обработка фото/видео и отправка заявки
@partner_router.message(StateFilter(PartnerApplicationState.waiting_for_photos),
                        F.content_type.in_({"photo", "video", "text"}))
async def finalize_application(message: Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    region = user_data.get("region")
    address_input = user_data.get("address")
    address_found = user_data.get("address_found", "Не найдено")
    map_link = user_data.get("map_link", "Нет данных")
    user_id = message.from_user.id  # Получаем ID пользователя

    # Обработка фото или видео
    media_group = []
    if message.photo:
        media_group.append(InputMediaPhoto(media=message.photo[-1].file_id, caption="Фото помещения"))
    elif message.video:
        media_group.append(InputMediaVideo(media=message.video.file_id, caption="Видео помещения"))

    # Формирование сообщения для поддержки
    support_message = (
        "🔔 <b>Новая заявка от партнёра</b>\n\n"
        f"👤 <b>ФИО:</b> {user_data['full_name']}\n"
        f"📞 <b>Телефон:</b> {user_data['phone']}\n"
        f"📍 <b>Регион:</b> {region}\n"
        f"🏠 <b>Адрес:</b> {address_input}\n"
        f"🗺️ <b>Найденный адрес:</b> {address_found}\n"
        f"🔗 <b>Ссылка на карту:</b> <a href='{map_link}'>Открыть в Яндекс.Картах</a>\n"
        f"🆔 <b>ID пользователя:</b> {user_id}"
    )

    # Отправка данных в чат поддержки
    await bot.send_message(PARTNER_CHAT_ID, support_message, parse_mode="HTML")
    if media_group:
        await bot.send_media_group(PARTNER_CHAT_ID, media_group)

    # Подтверждение пользователю
    await message.answer("✅ Ваша заявка успешно отправлена! Спасибо за Ваше сообщение, мы ознакомимся с ним и в случае заинтересованности обязательно с Вами свяжемся.")
    await state.clear()


# Обработка нажатия кнопки "Пропустить"
@partner_router.callback_query(lambda c: c.data == "skip_photos")
async def skip_photos(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    region = user_data.get("region")
    address_input = user_data.get("address")
    address_found = user_data.get("address_found", "Не найдено")
    map_link = user_data.get("map_link", "Нет данных")
    user_id = callback.from_user.id  # Получаем ID пользователя

    # Формирование сообщения для поддержки
    support_message = (
        "🔔 <b>Новая заявка от партнёра</b>\n\n"
        f"👤 <b>ФИО:</b> {user_data['full_name']}\n"
        f"📞 <b>Телефон:</b> {user_data['phone']}\n"
        f"📍 <b>Регион:</b> {region}\n"
        f"🏠 <b>Адрес:</b> {address_input}\n"
        f"🗺️ <b>Найденный адрес:</b> {address_found}\n"
        f"🔗 <b>Ссылка на карту:</b> <a href='{map_link}'>Открыть в Яндекс.Картах</a>\n"
        f"🖼️ <b>Фото или видео:</b> <i>Не предоставлено</i>\n"
        f"🆔 <b>ID пользователя:</b> {user_id}"
    )

    # Отправка данных в чат поддержки
    await bot.send_message(PARTNER_CHAT_ID, support_message, parse_mode="HTML")

    # Подтверждение пользователю
    await callback.message.edit_text(
        "✅ Ваша заявка отправлена без фото или видео. Спасибо за Ваше сообщение, мы ознакомимся с ним и в случае заинтересованности обязательно с Вами свяжемся."
    )
    await state.clear()


# Обработка ответа оператора в чате поддержки
@partner_router.message()
async def forward_partner_response(message: Message, bot: Bot):
    if message.chat.id == PARTNER_CHAT_ID:  # Проверяем, что сообщение пришло из чата поддержки
        if not message.reply_to_message:
            await message.answer("⚠ Ошибка: Ответ должен быть на сообщение заявки.")
            return

        # Ищем ID пользователя в исходном сообщении
        match = re.search(r"ID пользователя: (\d+)", message.reply_to_message.text)
        if not match:
            await message.answer("⚠ Ошибка: Не удалось найти ID пользователя в сообщении заявки.")
            return

        user_id = int(match.group(1))  # Получаем ID пользователя

        # Отправляем ответ пользователю
        try:
            await bot.send_message(
                user_id, f"📩 <b>Ответ на вашу заявку:</b>\n\n{message.text}", parse_mode="HTML"
            )
            await message.answer("✅ Ответ отправлен пользователю.")
        except Exception as e:
            await message.answer(f"❌ Ошибка отправки ответа: {e}")

