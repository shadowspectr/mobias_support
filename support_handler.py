# support_handler.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import logging
from datetime import datetime
from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import get_back_to_menu_keyboard, get_start_keyboard

# --- КОНФИГУРАЦИЯ ---
SUPPORT_TICKETS_CHAT_ID = -4961897884 # ID ОСНОВНОЙ ГРУППЫ ПОДДЕРЖКИ
ADMIN_USER_ID = 12345678 # Замените на ID администратора

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

# --- Словари для активных диалогов ---
# {client_id: support_agent_id}
active_dialogs = {}
# {support_agent_id: client_id}
support_to_user_map = {}

router = Router()


# 1. НАЧАЛО ДИАЛОГА: Пользователь нажимает кнопку "Задать вопрос"
@router.message(F.text == "❓ Задать вопрос")
async def start_support_dialog(message: types.Message, state: FSMContext):
    # Если пользователь уже в активном диалоге, не даем начать новый
    if message.from_user.id in active_dialogs:
        await message.answer("Вы уже ведете диалог со специалистом. Пожалуйста, завершите его, прежде чем начинать новый.")
        return
    await state.clear()
    await message.answer(
        "💬 Пожалуйста, опишите ваш вопрос или проблему одним сообщением. Можете приложить фото или видео.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await state.set_state(SupportConversation.waiting_for_first_message)


# 2. ПЕРВОЕ СООБЩЕНИЕ ОТ КЛИЕНТА
@router.message(SupportConversation.waiting_for_first_message)
async def process_first_question(message: types.Message, state: FSMContext, bot: Bot):
    user = message.from_user
    ticket_id = f"T-{user.id}-{datetime.now().strftime('%H%M')}"
    await state.update_data(ticket_id=ticket_id)

    ticket_caption = (
        f"🎫 <b>Новое обращение #{ticket_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> @{user.username if user.username else 'Не указан'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>"
    )
    try:
        start_dialog_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💬 Начать диалог с клиентом",
                callback_data=f"start_dialog:{user.id}:{ticket_id}"
            )]
        ])
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, ticket_caption)
        await message.copy_to(
            chat_id=SUPPORT_TICKETS_CHAT_ID,
            reply_markup=start_dialog_button
        )
        await message.answer(QUICK_RESPONSE_FIRST)
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
    try:
        await bot.send_message(
            SUPPORT_TICKETS_CHAT_ID,
            f"📎 <b>Дополнение к тикету #{ticket_id}</b>"
        )
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        await message.answer(QUICK_RESPONSE_SECOND, reply_markup=get_start_keyboard())
        logging.info(f"Получена доп. информация по тикету {ticket_id}")
    except Exception as e:
        logging.error(f"Не удалось переслать доп. инфо по тикету #{ticket_id}: {e}")
        await bot.send_message(ADMIN_USER_ID, f"Ошибка пересылки доп. инфо для {ticket_id}: {e}")
        await message.answer("Не удалось отправить дополнительную информацию. Специалист скоро свяжется с вами по основному вопросу.")
    await state.clear()


# 4. СОТРУДНИК НАЧИНАЕТ ДИАЛОГ
@router.callback_query(F.data.startswith("start_dialog:"))
async def handle_start_dialog(callback: types.CallbackQuery, bot: Bot):
    _, user_id_str, ticket_id = callback.data.split(":")
    user_id = int(user_id_str)
    support_agent = callback.from_user

    if user_id in active_dialogs:
        await callback.answer("Другой сотрудник уже начал диалог с этим клиентом.", show_alert=True)
        return
    if support_agent.id in support_to_user_map:
        await callback.answer("Вы уже ведете диалог с другим клиентом. Завершите его командой /end, чтобы взять новый.", show_alert=True)
        return

    # === УСТАНОВКА СВЯЗИ ===
    active_dialogs[user_id] = support_agent.id
    support_to_user_map[support_agent.id] = user_id
    logging.info(f"Установлена связь: Клиент {user_id} <-> Специалист {support_agent.id} (Тикет {ticket_id})")
    logging.info(f"active_dialogs: {active_dialogs}")
    logging.info(f"support_to_user_map: {support_to_user_map}")

    original_message_text = callback.message.html_text if callback.message.html_text else callback.message.text

    await callback.message.edit_text(
        f"{original_message_text}\n\n"
        f"✅ <b>В работе у:</b> {support_agent.full_name} (@{support_agent.username or ''})",
    )
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


# 5. ОСНОВНАЯ ЛОГИКА ПЕРЕСЫЛКИ СООБЩЕНИЙ (ПОЛНОСТЬЮ ПЕРЕРАБОТАНА)
@router.message(lambda message: message.from_user.id in active_dialogs or message.from_user.id in support_to_user_map)
async def message_relay(message: types.Message, bot: Bot):
    sender_id = message.from_user.id
    logging.info(f"Relay: Получено сообщение от {sender_id}. Проверяем маршрут.")

    # Сценарий 1: Сообщение от клиента, который находится в активном диалоге
    if sender_id in active_dialogs:
        recipient_id = active_dialogs[sender_id]
        logging.info(f"Маршрут: Клиент ({sender_id}) -> Специалист ({recipient_id})")
        
        # Проверка на самоотправку (на всякий случай)
        if sender_id == recipient_id:
            logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: Обнаружена попытка отправки сообщения самому себе! Клиент: {sender_id}")
            return
            
        try:
            await message.copy_to(chat_id=recipient_id)
        except Exception as e:
            logging.error(f"Ошибка пересылки от клиента ({sender_id}) специалисту ({recipient_id}): {e}")
            await message.answer("Не удалось доставить ваше сообщение специалисту. Пожалуйста, попробуйте еще раз.")
        return

    # Сценарий 2: Сообщение от специалиста, который ведет диалог
    elif sender_id in support_to_user_map:
        recipient_id = support_to_user_map[sender_id]
        logging.info(f"Маршрут: Специалист ({sender_id}) -> Клиент ({recipient_id})")

        # Проверка на самоотправку
        if sender_id == recipient_id:
            logging.error(f"КРИТИЧЕСКАЯ ОШИБКА: Обнаружена попытка отправки сообщения самому себе! Специалист: {sender_id}")
            return
            
        # Проверка команды завершения диалога
        if message.text and message.text.lower().startswith('/end'):
            logging.info(f"Специалист {sender_id} завершает диалог с клиентом {recipient_id}.")
            
            # === РАЗРЫВ СВЯЗИ ===
            del active_dialogs[recipient_id]
            del support_to_user_map[sender_id]
            logging.info(f"Связь разорвана. active_dialogs: {active_dialogs}, support_to_user_map: {support_to_user_map}")
            
            await bot.send_message(recipient_id, "Диалог со специалистом поддержки завершен. Спасибо за обращение!", reply_markup=get_start_keyboard())
            await message.answer("Вы успешно завершили диалог. Чтобы взять новый тикет, перейдите в группу.")
            return
            
        # Пересылка обычного сообщения клиенту
        try:
            await message.copy_to(chat_id=recipient_id)
        except Exception as e:
            logging.error(f"Ошибка пересылки от специалиста ({sender_id}) клиенту ({recipient_id}): {e}")
            await message.answer("Не удалось доставить ваше сообщение клиенту. Возможно, он заблокировал бота или произошла ошибка.")
        return
    
    # Этот блок не должен сработать из-за фильтра в декораторе, но он здесь для надежности
    else:
        logging.warning(f"Relay: Сообщение от {sender_id} прошло фильтр, но не подошло ни под один сценарий.")