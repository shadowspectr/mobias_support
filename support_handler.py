from aiogram import Router, types, Bot, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import asyncio
from datetime import datetime

# Состояния для машины состояний
class SupportState(StatesGroup):
    waiting_for_first_question = State()
    waiting_for_additional_info = State()
    in_support_dialog = State()

callback_router = Router()

# ID чата для тикетов (основная группа поддержки)
SUPPORT_TICKETS_CHAT_ID = -4961897884

# Словари для управления диалогами
# {user_id: {'support_user_id': int, 'chat_id': int, 'ticket_id': str}}
active_dialogs = {}
# Словарь для предотвращения спама при загрузке файлов {user_id: last_message_time}
file_upload_cooldown = {}

# Быстрые ответы
QUICK_RESPONSES = {
    "first": """🤖 Спасибо за обращение! 

Ваш вопрос принят в обработку. Наши специалисты ответят в ближайшее время.

❓ Если у вас есть дополнительная информация по вашему вопросу, можете добавить её сейчас.""",
    
    "second": """✅ Дополнительная информация принята!

Мы свяжемся с вами в ближайшее время для решения вашего вопроса.

⏰ Обычное время ответа: до 30 минут в рабочее время."""
}

# Обработчик для кнопки "Обратиться в поддержку"
@callback_router.callback_query(lambda c: c.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "💬 Опишите ваш вопрос или проблему. Мы обязательно поможем!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="open_main")]
        ])
    )
    await state.set_state(SupportState.waiting_for_first_question)

# Обработчик для текстовой кнопки "Обратиться в поддержку"
@callback_router.message(F.text == "❓ Обратиться в поддержку")
async def support_start_text(message: Message, state: FSMContext):
    await message.answer(
        "💬 Опишите ваш вопрос или проблему. Мы обязательно поможем!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="open_main")]
        ])
    )
    await state.set_state(SupportState.waiting_for_first_question)

# Первый вопрос от клиента
@callback_router.message(SupportState.waiting_for_first_question)
async def handle_first_question(message: Message, state: FSMContext, bot: Bot):
    # Проверка на спам при загрузке файлов
    if not await check_file_upload_cooldown(message, bot):
        return
    
    try:
        # Создаем уникальный ID тикета
        ticket_id = f"T{datetime.now().strftime('%y%m%d%H%M%S')}"
        
        # Сохраняем данные тикета для возможного создания чата
        user_data = {
            'user_id': message.from_user.id,
            'username': message.from_user.username or 'без_username',
            'first_name': message.from_user.first_name or 'Пользователь',
            'ticket_id': ticket_id,
            'created_at': datetime.now()
        }
        
        # Отправляем тикет в основную группу поддержки
        ticket_text = f"""🎫 <b>Новый тикет #{ticket_id}</b>
👤 Пользователь: @{user_data['username']} (ID: {user_data['user_id']})
📅 Время: {user_data['created_at'].strftime('%d.%m.%Y %H:%M')}

<b>Вопрос:</b>"""
        
        # Отправляем заголовок тикета
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, ticket_text, parse_mode="HTML")
        
        # Копируем сообщение пользователя
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        
        # Кнопка для создания отдельного чата
        support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💬 Создать чат для диалога", 
                callback_data=f"create_dialog_{message.from_user.id}_{ticket_id}"
            )]
        ])
        
        await bot.send_message(
            SUPPORT_TICKETS_CHAT_ID,
            f"📋 Тикет #{ticket_id} создан",
            reply_markup=support_keyboard
        )
        
        # Первый быстрый ответ клиенту
        await message.answer(QUICK_RESPONSES["first"])
        
        # Переводим в состояние ожидания дополнительной информации
        await state.set_state(SupportState.waiting_for_additional_info)
        await state.update_data(ticket_id=ticket_id, user_data=user_data)
        
        logging.info(f"Создан тикет {ticket_id} для пользователя {message.from_user.id}")
        
    except Exception as e:
        logging.error(f"Ошибка создания тикета: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже или обратитесь по телефону.")

# Дополнительная информация от клиента
@callback_router.message(SupportState.waiting_for_additional_info)
async def handle_additional_info(message: Message, state: FSMContext, bot: Bot):
    # Проверка на спам при загрузке файлов
    if not await check_file_upload_cooldown(message, bot):
        return
    
    try:
        state_data = await state.get_data()
        ticket_id = state_data.get('ticket_id', 'Unknown')
        
        # Добавляем дополнительную информацию к тикету
        additional_text = f"""📎 <b>Дополнительная информация к тикету #{ticket_id}:</b>
👤 От: @{message.from_user.username or 'без_username'} (ID: {message.from_user.id})"""
        
        await bot.send_message(SUPPORT_TICKETS_CHAT_ID, additional_text, parse_mode="HTML")
        await message.copy_to(chat_id=SUPPORT_TICKETS_CHAT_ID)
        
        # Второй быстрый ответ клиенту
        await message.answer(QUICK_RESPONSES["second"])
        
        # Завершаем сбор информации
        await state.clear()
        
        logging.info(f"Получена дополнительная информация для тикета {ticket_id}")
        
    except Exception as e:
        logging.error(f"Ошибка обработки дополнительной информации: {e}")

# Обработчик создания отдельного чата для диалога
@callback_router.callback_query(lambda c: c.data.startswith("create_dialog_"))
async def create_support_dialog_chat(callback: CallbackQuery, bot: Bot):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        ticket_id = parts[3] if len(parts) > 3 else "Unknown"
        support_user_id = callback.from_user.id
        
        # Создаем новую группу для диалога
        chat_title = f"Диалог #{ticket_id} - {callback.from_user.first_name}"
        
        try:
            # Создаем группу (бот должен иметь права на создание групп)
            new_chat = await bot.create_group_chat(
                title=chat_title,
                user_ids=[support_user_id]  # Добавляем сотрудника поддержки
            )
            dialog_chat_id = new_chat.id
            
        except Exception as create_error:
            # Если не получается создать группу, используем обходной метод
            logging.warning(f"Не удалось создать группу: {create_error}")
            
            # Отправляем инструкцию сотруднику
            instruction_msg = await bot.send_message(
                support_user_id,
                f"💬 <b>Начат диалог с пользователем</b>\n\n"
                f"🎫 Тикет: #{ticket_id}\n"
                f"👤 Пользователь: {user_id}\n\n"
                f"<b>Инструкция:</b>\n"
                f"• Все ваши сообщения в этом чате будут пересылаться пользователю\n"
                f"• Сообщения пользователя будут приходить сюда\n"
                f"• Для завершения диалога напишите: <code>/end_{user_id}</code>\n\n"
                f"🔄 Диалог активирован!",
                parse_mode="HTML"
            )
            
            dialog_chat_id = support_user_id  # Используем личные сообщения
        
        # Сохраняем информацию об активном диалоге
        active_dialogs[user_id] = {
            'support_user_id': support_user_id,
            'chat_id': dialog_chat_id,
            'ticket_id': ticket_id,
            'created_at': datetime.now()
        }
        
        # Уведомляем в основной группе
        await callback.message.edit_text(
            f"✅ Диалог для тикета #{ticket_id} создан!\n"
            f"👨‍💼 Сотрудник: {callback.from_user.first_name}\n"
            f"💬 Чат ID: {dialog_chat_id}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="❌ Завершить диалог", 
                    callback_data=f"end_dialog_{user_id}"
                )]
            ])
        )
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            f"👨‍💼 С вами связался специалист поддержки!\n"
            f"🎫 Тикет: #{ticket_id}\n\n"
            f"Теперь вы можете общаться напрямую. Специалист получит все ваши сообщения."
        )
        
        await callback.answer("Диалог создан!")
        logging.info(f"Создан диалог для тикета {ticket_id}: {support_user_id} <-> {user_id}")
        
    except Exception as e:
        logging.error(f"Ошибка создания диалога: {e}")
        await callback.answer("Ошибка при создании диалога")

# Обработчик сообщений от сотрудников поддержки
@callback_router.message()
async def handle_support_messages(message: Message, bot: Bot):
    """Обрабатываем сообщения от сотрудников поддержки"""
    try:
        support_user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Ищем активный диалог для этого сотрудника
        user_id = None
        dialog_info = None
        
        for uid, info in active_dialogs.items():
            if (info['support_user_id'] == support_user_id and 
                info['chat_id'] == chat_id):
                user_id = uid
                dialog_info = info
                break
        
        if not user_id:
            # Возможно, это команда завершения диалога
            if message.text and message.text.startswith("/end_"):
                try:
                    end_user_id = int(message.text.split("_")[1])
                    if end_user_id in active_dialogs:
                        await end_dialog(end_user_id, bot, message)
                        return
                except (ValueError, IndexError):
                    pass
            return
        
        # Проверяем команду завершения
        if message.text and message.text == f"/end_{user_id}":
            await end_dialog(user_id, bot, message)
            return
        
        # Пересылаем сообщение пользователю
        await message.copy_to(chat_id=user_id)
        
        # Отправляем подтверждение сотруднику
        await bot.send_message(
            chat_id,
            f"✅ Отправлено пользователю {user_id}",
            reply_to_message_id=message.message_id
        )
        
        logging.info(f"Сообщение от {support_user_id} переслано пользователю {user_id}")
        
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения поддержки: {e}")

# Обработчик сообщений от пользователей в активном диалоге
@callback_router.message(lambda message: message.from_user.id in active_dialogs.keys())
async def handle_user_dialog_messages(message: Message, bot: Bot):
    """Пересылаем сообщения пользователей в чат диалога"""
    try:
        user_id = message.from_user.id
        dialog_info = active_dialogs[user_id]
        
        # Пересылаем сообщение в чат диалога
        await message.copy_to(chat_id=dialog_info['chat_id'])
        
        # Добавляем информацию о пользователе
        await bot.send_message(
            dialog_info['chat_id'],
            f"👤 От пользователя {user_id} (@{message.from_user.username or 'без_username'})\n"
            f"🎫 Тикет: #{dialog_info['ticket_id']}"
        )
        
        logging.info(f"Сообщение от пользователя {user_id} переслано в диалог {dialog_info['chat_id']}")
        
    except Exception as e:
        logging.error(f"Ошибка пересылки сообщения пользователя: {e}")

# Функция завершения диалога
async def end_dialog(user_id: int, bot: Bot, message: Message = None):
    """Завершает активный диалог"""
    try:
        if user_id not in active_dialogs:
            if message:
                await message.answer("Диалог не найден")
            return
        
        dialog_info = active_dialogs[user_id]
        ticket_id = dialog_info['ticket_id']
        
        # Удаляем из активных диалогов
        del active_dialogs[user_id]
        
        # Уведомляем сотрудника
        await bot.send_message(
            dialog_info['chat_id'],
            f"✅ Диалог завершен!\n🎫 Тикет #{ticket_id} закрыт."
        )
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            f"👨‍💼 Диалог завершен.\n🎫 Тикет #{ticket_id} закрыт.\n\n"
            f"Спасибо за обращение! Если у вас возникнут новые вопросы, обращайтесь снова."
        )
        
        # Уведомляем в основную группу
        await bot.send_message(
            SUPPORT_TICKETS_CHAT_ID,
            f"✅ Диалог по тикету #{ticket_id} завершен"
        )
        
        logging.info(f"Диалог для тикета {ticket_id} завершен")
        
    except Exception as e:
        logging.error(f"Ошибка завершения диалога: {e}")

# Обработчик кнопки завершения диалога
@callback_router.callback_query(lambda c: c.data.startswith("end_dialog_"))
async def end_dialog_callback(callback: CallbackQuery, bot: Bot):
    try:
        user_id = int(callback.data.split("_")[2])
        await end_dialog(user_id, bot)
        await callback.answer("Диалог завершен")
    except Exception as e:
        logging.error(f"Ошибка завершения диалога через кнопку: {e}")
        await callback.answer("Ошибка завершения диалога")

# Функция проверки кулдауна для файлов
async def check_file_upload_cooldown(message: Message, bot: Bot, cooldown_seconds: int = 3) -> bool:
    """Предотвращает спам при загрузке нескольких файлов"""
    user_id = message.from_user.id
    current_time = asyncio.get_event_loop().time()
    
    # Если это не медиа-файл, пропускаем проверку
    if not (message.photo or message.document or message.video or message.audio or message.voice):
        return True
    
    # Проверяем кулдаун
    if user_id in file_upload_cooldown:
        time_since_last = current_time - file_upload_cooldown[user_id]
        if time_since_last < cooldown_seconds:
            logging.info(f"Кулдаун для пользователя {user_id}, пропускаем сообщение")
            return False
    
    # Обновляем время последнего сообщения
    file_upload_cooldown[user_id] = current_time
    return True

# Команда для завершения всех диалогов (экстренная)
@callback_router.message(lambda message: message.text == "/end_all_dialogs")
async def end_all_dialogs(message: Message, bot: Bot):
    """Завершить все активные диалоги (для админов)"""
    try:
        count = len(active_dialogs)
        
        # Завершаем все диалоги
        for user_id in list(active_dialogs.keys()):
            await end_dialog(user_id, bot)
        
        await message.answer(f"✅ Завершено {count} активных диалогов")
        logging.info(f"Все диалоги завершены пользователем {message.from_user.id}")
        
    except Exception as e:
        logging.error(f"Ошибка завершения всех диалогов: {e}")