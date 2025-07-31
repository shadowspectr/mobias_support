from aiogram import Router, types, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

# Состояния для машины состояний
class SupportState(StatesGroup):
    waiting_for_question = State()

callback_router = Router()

# ID чата техподдержки
SUPPORT_CHAT_ID = -1002837608854

# Словарь для хранения соответствия между сообщениями и пользователями
# Ключ: message_id сообщения с [ID:...], Значение: user_id
support_messages = {}

# Обработчик для кнопки "Обратиться в поддержку"
@callback_router.callback_query(lambda c: c.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🛠 Пожалуйста, опишите вашу проблему или задайте вопрос.")
    await state.set_state(SupportState.waiting_for_question)

# Обработчик получения вопроса от пользователя
@callback_router.message(SupportState.waiting_for_question)
async def receive_support_question(message: Message, state: FSMContext, bot: Bot):
    try:
        # 1. Пересылаем сообщение пользователя в поддержку (с сохранением всех вложений)
        forwarded_msg = await message.forward(chat_id=SUPPORT_CHAT_ID)
        
        # 2. Отправляем служебное сообщение с ID пользователя
        id_message = await bot.send_message(
            SUPPORT_CHAT_ID, 
            f"[ID:{message.from_user.id}] @{message.from_user.username or 'нет_username'}"
        )
        
        # 3. Сохраняем связь между служебным сообщением и пользователем
        support_messages[id_message.message_id] = message.from_user.id
        
        await message.answer("Ваше сообщение отправлено в техподдержку 💬\nСкоро с вами свяжется специалист.")
        await state.clear()
        
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в поддержку: {e}")
        await message.answer("Произошла ошибка при отправке сообщения. Попробуйте позже.")

# Обработчик ответов от техподдержки
@callback_router.message(lambda message: message.chat.id == SUPPORT_CHAT_ID)
async def forward_support_response(message: Message, bot: Bot):
    try:
        # Ищем последний ID пользователя из служебных сообщений
        user_id = None
        
        # Проверяем, является ли это служебным сообщением с ID
        if message.text and message.text.startswith("[ID:"):
            # Это служебное сообщение, не пересылаем его
            return
        
        # Ищем ID пользователя в недавних сообщениях
        # Берем message_id текущего сообщения и ищем ближайшее служебное сообщение
        current_msg_id = message.message_id
        
        # Проверяем несколько предыдущих сообщений
        for check_id in range(current_msg_id - 1, max(0, current_msg_id - 10), -1):
            if check_id in support_messages:
                user_id = support_messages[check_id]
                break
        
        # Если не нашли в кэше, пытаемся найти по тексту в недавних сообщениях
        if not user_id:
            # Здесь можно добавить логику поиска по reply_to_message
            if message.reply_to_message and message.reply_to_message.text:
                reply_text = message.reply_to_message.text
                if reply_text.startswith("[ID:"):
                    try:
                        # Извлекаем ID из текста вида "[ID:123456] @username"
                        id_part = reply_text.split("]")[0][4:]  # Убираем "[ID:" и берем до "]"
                        user_id = int(id_part)
                    except (ValueError, IndexError):
                        pass
        
        if user_id:
            # Пересылаем ответ пользователю (сохраняем все вложения)
            await message.copy_to(chat_id=user_id)
            logging.info(f"Ответ от поддержки переслан пользователю {user_id}")
        else:
            logging.warning("Не удалось определить ID пользователя для ответа")
            # Отправляем уведомление в чат поддержки
            await bot.send_message(
                SUPPORT_CHAT_ID, 
                "⚠️ Не удалось определить получателя. Ответьте на сообщение с [ID:...] или укажите ID вручную."
            )
            
    except Exception as e:
        logging.error(f"Ошибка при пересылке ответа от поддержки: {e}")

# Дополнительный обработчик для команды поддержки (если нужно очистить кэш)
@callback_router.message(lambda message: message.chat.id == SUPPORT_CHAT_ID and message.text and message.text.startswith("/clear_cache"))
async def clear_support_cache(message: Message):
    global support_messages
    support_messages.clear()
    await message.answer("Кэш служебных сообщений очищен.")