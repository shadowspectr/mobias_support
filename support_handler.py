# support_handler.py (ПОЛНЫЙ ФАЙЛ)
import logging
import asyncio
from datetime import datetime
from aiogram import Router, types, Bot, F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import get_back_to_menu_keyboard, get_start_keyboard, get_end_dialog_keyboard
# ===== ИЗМЕНЕНИЕ: Импортируем все константы =====
from constants import (
    SUPPORT_BUTTON_TEXT, KNOWN_BUTTONS, END_DIALOG_BUTTON_TEXT,
    SUPPORT_TICKETS_CHAT_ID, ADMIN_USER_ID, DIALOG_TIMEOUT_SECONDS
)

# --- КОНФИГУРАЦИЯ ---
SUPPORT_TICKETS_CHAT_ID = -4961897884
ADMIN_USER_ID = 12345678 # Замените на ваш ID для отладки
DIALOG_TIMEOUT_SECONDS = 5 * 3600  # 5 часов

# --- ТЕКСТЫ БЫСТРЫХ ОТВЕТОВ ---
QUICK_RESPONSE_FIRST = """🤖 Спасибо за обращение! 

Ваш вопрос принят в обработку. Наши специалисты скоро подключатся к диалогу.

Если у вас есть дополнительная информация (например, фото или видео), можете добавить её следующим сообщением."""

QUICK_RESPONSE_SECOND = """✅ Дополнительная информация принята!

Ожидайте, скоро с вами свяжется наш специалист."""

# --- Состояния FSM ---
class SupportConversation(StatesGroup):
    waiting_for_first_message = State()
    waiting_for_additional_info = State()

# --- Словари для диалогов и задач тайм-аута ---
active_dialogs = {}
support_to_user_map = {}
timeout_tasks = {} # {user_id: asyncio.Task}

router = Router()

async def _end_dialog(user_id: int, bot: Bot, reason: str = "Диалог завершен."):
    if user_id not in active_dialogs: return
    support_agent_id = active_dialogs.get(user_id)
    if user_id in timeout_tasks:
        timeout_tasks[user_id].cancel()
        del timeout_tasks[user_id]
    if user_id in active_dialogs: del active_dialogs[user_id]
    if support_agent_id and support_agent_id in support_to_user_map: del support_to_user_map[support_agent_id]
    try:
        await bot.send_message(user_id, f"❗️ {reason}\n\nЕсли у вас остались вопросы, вы можете задать их снова.", reply_markup=get_start_keyboard())
        if support_agent_id: await bot.send_message(support_agent_id, f"✅ Диалог с пользователем {user_id} завершен. Причина: {reason}")
        logging.info(f"Диалог для {user_id} и {support_agent_id} завершен. Причина: {reason}")
    except Exception as e: logging.error(f"Ошибка при отправке уведомлений о завершении диалога {user_id}: {e}")

async def _dialog_timeout_watcher(user_id: int, bot: Bot):
    try:
        await asyncio.sleep(DIALOG_TIMEOUT_SECONDS)
        logging.info(f"Сработал тайм-аут 5 часов для пользователя {user_id}. Закрываю диалог.")
        await _end_dialog(user_id, bot, reason="Диалог был автоматически завершен из-за отсутствия активности.")
    except asyncio.CancelledError: logging.info(f"Хранитель тайм-аута для {user_id} был успешно отменен.")
    except Exception as e: logging.error(f"Ошибка в хранителе тайм-аута для {user_id}: {e}")

@router.message(F.text == SUPPORT_BUTTON_TEXT)
async def start_support_dialog(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in {SupportConversation.waiting_for_first_message, SupportConversation.waiting_for_additional_info}:
        await message.answer("Вы уже находитесь в процессе создания обращения. Просто отправьте ваше сообщение.")
        return
    if message.from_user.id in active_dialogs:
        await message.answer("Вы уже ведете диалог со специалистом. Пожалуйста, завершите его, прежде чем начинать новый.")
        return
    await state.clear()
    await message.answer("💬 Пожалуйста, опишите ваш вопрос или проблему одним сообщением. Можете приложить фото или видео.", reply_markup=get_back_to_menu_keyboard())
    await state.set_state(SupportConversation.waiting_for_first_message)

@router.message(SupportConversation.waiting_for_first_message)
async def process_first_question(message: types.Message, state: FSMContext, bot: Bot):
    user = message.from_user
    ticket_id = f"T-{user.id}-{datetime.now().strftime('%H%M')}"
    await state.update_data(ticket_id=ticket_id)
    ticket_caption = (f"🎫 <b>Новое обращение #{ticket_id}</b>\n\n👤 <b>Клиент:</b> {user.full_name}\n🔗 <b>Username:</b> @{user.username if user.username else 'Не указан'}\n🆔 <b>User ID:</b> <code>{user.id}</code>")
    try:
        start_dialog_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Начать диалог с клиентом", callback_data=f"start_dialog:{user.id}:{ticket_id}")]])
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, ticket_caption, reply_markup=start_dialog_button)
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        await message.answer(QUICK_RESPONSE_FIRST)
        await state.set_state(SupportConversation.waiting_for_additional_info)
        logging.info(f"Создан тикет {ticket_id} для пользователя {user.id}")
    except Exception as e:
        logging.error(f"Не удалось создать тикет #{ticket_id}: {e}")
        await bot.send_message(ADMIN_USER_ID, f"Ошибка создания тикета для {user.id}: {e}")
        await message.answer("Произошла ошибка при создании вашего обращения.")
        await state.clear()

@router.message(SupportConversation.waiting_for_additional_info, lambda message: message.text not in KNOWN_BUTTONS)
async def process_additional_info(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data.get('ticket_id', 'N/A')
    try:
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, f"📎 <b>Дополнение к тикету #{ticket_id}</b>")
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        await message.answer(QUICK_RESPONSE_SECOND)
        logging.info(f"Получена доп. информация по тикету {ticket_id}.")
    except Exception as e:
        logging.error(f"Не удалось переслать доп. инфо по тикету #{ticket_id}: {e}")
        await bot.send_message(ADMIN_USER_ID, f"Ошибка пересылки доп. инфо для {ticket_id}: {e}")
        await message.answer("Не удалось отправить дополнительную информацию.")

@router.callback_query(F.data.startswith("start_dialog:"))
async def handle_start_dialog(callback: types.CallbackQuery, bot: Bot, dispatcher: Dispatcher):
    _, user_id_str, ticket_id = callback.data.split(":")
    user_id = int(user_id_str)
    support_agent = callback.from_user
    if user_id in active_dialogs:
        await callback.answer("Другой сотрудник уже начал диалог с этим клиентом.", show_alert=True)
        return
    if support_agent.id in support_to_user_map:
        await callback.answer("Вы уже ведете диалог с другим клиентом. Завершите его командой /end.", show_alert=True)
        return
    user_state: FSMContext = dispatcher.fsm.resolve_context(bot, chat_id=user_id, user_id=user_id)
    await user_state.clear()
    active_dialogs[user_id] = support_agent.id
    support_to_user_map[support_agent.id] = user_id
    task = asyncio.create_task(_dialog_timeout_watcher(user_id, bot))
    timeout_tasks[user_id] = task
    logging.info(f"Запущена задача тайм-аута для пользователя {user_id}.")
    await callback.message.edit_text(f"{callback.message.html_text}\n\n✅ <b>В работе у:</b> {support_agent.full_name} (@{support_agent.username or ''})", reply_markup=None)
    await bot.send_message(user_id, "👨‍💼 Здравствуйте! С вами на связи специалист поддержки. Теперь вы можете задать все уточняющие вопросы здесь.", reply_markup=get_end_dialog_keyboard())
    await bot.send_message(support_agent.id, f"Вы начали диалог с клиентом по тикету #{ticket_id}.\nВсе ваши сообщения в этом чате будут пересылаться клиенту.\nЧтобы завершить диалог, отправьте команду: /end")
    await callback.answer("Вы начали диалог. Клиент уведомлен.")

@router.message(F.text == END_DIALOG_BUTTON_TEXT)
async def user_ends_dialog(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if user_id not in active_dialogs:
        await message.answer("У вас нет активных диалогов.", reply_markup=get_start_keyboard())
        return
    await _end_dialog(user_id, bot, reason="Диалог завершен пользователем.")

@router.message(lambda message: (message.from_user.id in active_dialogs or message.from_user.id in support_to_user_map) and message.chat.id != SUPPORT_TICKETS_CHAT_ID)
async def message_relay(message: types.Message, bot: Bot):
    sender_id = message.from_user.id
    if sender_id in active_dialogs:
        if message.text and message.text.lower().startswith('/end'):
            await _end_dialog(sender_id, bot, reason="Диалог завершен пользователем.")
            return
        if sender_id in timeout_tasks: timeout_tasks[sender_id].cancel()
        task = asyncio.create_task(_dialog_timeout_watcher(sender_id, bot))
        timeout_tasks[sender_id] = task
        logging.info(f"Активность от пользователя {sender_id}. Таймер тайм-аута перезапущен.")
        recipient_id = active_dialogs[sender_id]
        try: await message.copy_to(chat_id=recipient_id)
        except Exception as e:
            logging.error(f"Ошибка пересылки от клиента ({sender_id}) специалисту ({recipient_id}): {e}")
            await message.answer("Не удалось доставить ваше сообщение специалисту.")
        return
    elif sender_id in support_to_user_map:
        user_id = support_to_user_map[sender_id]
        if message.text and message.text.lower().startswith('/end'):
            await _end_dialog(user_id, bot, reason="Диалог завершен специалистом.")
            return
        try: await message.copy_to(chat_id=user_id)
        except Exception as e:
            logging.error(f"Ошибка пересылки от специалиста ({sender_id}) клиенту ({user_id}): {e}")
            await message.answer("Не удалось доставить ваше сообщение клиенту.")
        return