# support_handler.py
import logging
from datetime import datetime
from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import get_back_to_menu_keyboard, get_start_keyboard

# --- КОНФИГУРАЦИЯ ---
SUPPORT_TICKETS_CHAT_ID = -4961897884  # ID ОСНОВНОЙ ГРУППЫ ПОДДЕРЖКИ
ADMIN_USER_ID = 521620770 # Замените на ID администратора для получения уведомлений об ошибках

# --- ТЕКСТЫ БЫСТРЫХ ОТВЕТОВ (можно легко изменить) ---
QUICK_RESPONSE_FIRST = """🤖 Спасибо за обращение! 

Ваш вопрос принят в обработку. Наши специалисты скоро подключатся к диалогу.

Если у вас есть дополнительная информация (например, фото или видео), можете добавить её следующим сообщением."""

QUICK_RESPONSE_SECOND = """✅ Дополнительная информация принята!

Ожидайте, скоро с вами свяжется наш специалист."""

# --- Состояния FSM для ведения клиента ---
class SupportConversation(StatesGroup):
    waiting_for_first_message = State()
    waiting_for_additional_info = State()

# --- Словарь для хранения активных диалогов ---
# {user_id: support_chat_id}
active_dialogs = {}
# {support_chat_id: user_id} - для быстрой обратной связи
support_to_user_map = {}

router = Router()


# 1. НАЧАЛО ДИАЛОГА: Пользователь нажимает кнопку "Задать вопрос"
@router.message(F.text == "❓ Задать вопрос")
async def start_support_dialog(message: types.Message, state: FSMContext):
    await state.clear() # На случай, если пользователь был в другом состоянии
    await message.answer(
        "💬 Пожалуйста, опишите ваш вопрос или проблему одним сообщением. Можете приложить фото или видео.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.set_state(SupportConversation.waiting_for_first_message)


# 2. ПЕРВОЕ СООБЩЕНИЕ ОТ КЛИЕНТА: Прием вопроса и создание тикета
@router.message(SupportConversation.waiting_for_first_message)
async def process_first_question(message: types.Message, state: FSMContext, bot: Bot):
    user = message.from_user
    ticket_id = f"T-{user.id}-{datetime.now().strftime('%H%M')}"

    # Сохраняем данные для диалога
    await state.update_data(ticket_id=ticket_id)

    ticket_caption = (
        f"🎫 <b>Новое обращение #{ticket_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> @{user.username if user.username else 'Не указан'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>"
    )

    try:
        # Создаем кнопку для начала диалога
        start_dialog_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💬 Начать диалог с клиентом",
                callback_data=f"start_dialog_{user.id}_{ticket_id}"
            )]
        ])

        # Отправляем сообщение-тикет в группу поддержки
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, ticket_caption, parse_mode="HTML")
        await message.copy_to(
            chat_id=SUPPORT_TICKETS_CHAT_ID,
            reply_markup=start_dialog_button
        )
        
        # Отправляем быстрый ответ клиенту
        await message.answer(QUICK_RESPONSE_FIRST)
        
        # Переводим в следующее состояние
        await state.set_state(SupportConversation.waiting_for_additional_info)
        logging.info(f"Создан тикет {ticket_id} для пользователя {user.id}")

    except Exception as e:
        logging.error(f"Не удалось создать тикет #{ticket_id} для {user.id}: {e}")
        await bot.send_message(ADMIN_USER_ID, f"Ошибка создания тикета для {user.id}: {e}")
        await message.answer("Произошла ошибка при создании вашего обращения. Пожалуйста, попробуйте позже.")
        await state.clear()


# 3. ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ОТ КЛИЕНТА
@router.message(SupportConversation.waiting_for_additional_info)
async def process_additional_info(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data.get('ticket_id', 'N/A')
    
    # Пересылаем доп. информацию в группу
    try:
        await bot.send_message(
            SUPPORT_TICKETS_CHAT_ID,
            f"📎 <b>Дополнение к тикету #{ticket_id}</b>"
        )
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        
        # Отправляем второй быстрый ответ
        await message.answer(QUICK_RESPONSE_SECOND, reply_markup=get_start_keyboard())
        logging.info(f"Получена доп. информация по тикету {ticket_id}")

    except Exception as e:
        logging.error(f"Не удалось переслать доп. инфо по тикету #{ticket_id}: {e}")
        await bot.send_message(ADMIN_USER_ID, f"Ошибка пересылки доп. инфо для {ticket_id}: {e}")
        await message.answer("Не удалось отправить дополнительную информацию. Специалист скоро свяжется с вами по основному вопросу.")

    # Очищаем состояние, т.к. бот свою задачу по сбору информации выполнил
    await state.clear()


# 4. СОТРУДНИК НАЧИНАЕТ ДИАЛОГ: Нажатие кнопки в группе
@router.callback_query(F.data.startswith("start_dialog_"))
async def handle_start_dialog(callback: types.CallbackQuery, bot: Bot):
    _, user_id_str, ticket_id = callback.data.split("_")
    user_id = int(user_id_str)
    support_agent = callback.from_user

    # Проверяем, не ведется ли уже диалог с этим клиентом
    if user_id in active_dialogs:
        await callback.answer("Другой сотрудник уже начал диалог с этим клиентом.", show_alert=True)
        return

    # Регистрируем активный диалог
    active_dialogs[user_id] = support_agent.id
    support_to_user_map[support_agent.id] = user_id
    
    logging.info(f"Сотрудник {support_agent.id} начал диалог с клиентом {user_id} (тикет {ticket_id})")

    # Редактируем сообщение в группе, чтобы показать, кто взял тикет
    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"✅ <b>В работе у:</b> {support_agent.full_name} (@{support_agent.username or ''})",
        parse_mode="HTML"
    )

    # Отправляем уведомления о начале диалога
    await bot.send_message(
        user_id,
        "👨‍💼 Здравствуйте! С вами на связи специалист поддержки. Теперь вы можете задать все уточняющие вопросы здесь."
    )
    await bot.send_message(
        support_agent.id,
        f"Вы начали диалог с клиентом по тикету #{ticket_id}.\n"
        f"Все ваши сообщения в этом чате будут пересылаться клиенту.\n"
        f"Чтобы завершить диалог, отправьте команду: /end"
    )
    await callback.answer("Вы начали диалог. Клиент уведомлен.")


# 5. ОСНОВНАЯ ЛОГИКА ПЕРЕСЫЛКИ СООБЩЕНИЙ
@router.message()
async def message_relay(message: types.Message, bot: Bot, state: FSMContext):
    # Если это сообщение от клиента, который в активном диалоге
    if message.from_user.id in active_dialogs:
        support_chat_id = active_dialogs[message.from_user.id]
        try:
            await message.copy_to(chat_id=support_chat_id)
        except Exception as e:
            logging.error(f"Не удалось переслать сообщение от клиента {message.from_user.id} сотруднику {support_chat_id}: {e}")
            await message.answer("Не удалось доставить ваше сообщение. Попробуйте еще раз.")
        return

    # Если это сообщение от сотрудника поддержки, который ведет диалог
    if message.from_user.id in support_to_user_map:
        user_id = support_to_user_map[message.from_user.id]

        # Команда для завершения диалога
        if message.text.lower() == '/end':
            # Удаляем диалог из словарей
            del active_dialogs[user_id]
            del support_to_user_map[message.from_user.id]
            
            await bot.send_message(user_id, "Диалог со специалистом поддержки завершен. Спасибо за обращение!")
            await message.answer("Вы успешно завершили диалог. Чтобы взять новый тикет, перейдите в группу.")
            logging.info(f"Сотрудник {message.from_user.id} завершил диалог с {user_id}")
            
            # Уведомление в основную группу (опционально)
            # await bot.send_message(SUPPORT_TICKETS_CHAT_ID, f"Диалог по тикету с клиентом {user_id} завершен.")
            return

        # Пересылаем сообщение клиенту
        try:
            await message.copy_to(chat_id=user_id)
        except Exception as e:
            logging.error(f"Не удалось переслать сообщение от сотрудника {message.from_user.id} клиенту {user_id}: {e}")
            await message.answer("Не удалось доставить ваше сообщение клиенту. Возможно, он заблокировал бота.")
        return
    
    # Если сообщение не попало ни в одно из состояний FSM или активных диалогов,
    # перенаправляем его в главный обработчик.
    # Для этого в main.py нужно будет вызвать fallback_handler.
    # Этот return необходим, чтобы aiogram не искал обработчики дальше по цепочке.
    # Если же мы хотим, чтобы такие сообщения обрабатывались как-то еще,
    # можно добавить здесь логику или просто убрать return.