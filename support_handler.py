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

# Обработчик ответов от техподдержки (только для ответов операторов)
@callback_router.message(lambda message: message.chat.id == SUPPORT_CHAT_ID and not _is_bot_message(message))
async def forward_support_response(message: Message, bot: Bot):
    try:
        # Проверяем, является ли это служебным сообщением с ID
        if message.text and message.text.startswith("[ID:"):
            # Это служебное сообщение, не пересылаем его
            return
        
        # Проверяем, не является ли это пересланным сообщением от пользователя
        if message.forward_from or message.forward_from_chat:
            # Это пересланное сообщение от пользователя, не пересылаем обратно
            return
            
        user_id = None
        
        # Сначала ищем по reply_to_message (приоритетный способ)
        if message.reply_to_message:
            # Проверяем, отвечает ли на служебное сообщение
            if message.reply_to_message.text and message.reply_to_message.text.startswith("[ID:"):
                try:
                    id_part = message.reply_to_message.text.split("]")[0][4:]
                    user_id = int(id_part)
                    logging.info(f"ID найден через reply_to_message: {user_id}")
                except (ValueError, IndexError):
                    pass
            # Проверяем, отвечает ли на пересланное сообщение от пользователя
            elif message.reply_to_message.forward_from:
                user_id = message.reply_to_message.forward_from.id
                logging.info(f"ID найден через forward_from: {user_id}")
        
        # Если не нашли через reply, ищем в кэше по недавним сообщениям
        if not user_id:
            current_msg_id = message.message_id
            for check_id in range(current_msg_id - 1, max(0, current_msg_id - 20), -1):
                if check_id in support_messages:
                    user_id = support_messages[check_id]
                    logging.info(f"ID найден в кэше: {user_id}")
                    break
        
        if user_id:
            # Пересылаем ответ пользователю (сохраняем все вложения)
            await message.copy_to(chat_id=user_id)
            logging.info(f"Ответ от поддержки переслан пользователю {user_id}")
        else:
            logging.warning("Не удалось определить ID пользователя для ответа")
            # Отправляем уведомление в чат поддержки
            await bot.send_message(
                SUPPORT_CHAT_ID, 
                "⚠️ Не удалось определить получателя. Ответьте на пересланное сообщение пользователя или на сообщение с [ID:...]"
            )
            
    except Exception as e:
        logging.error(f"Ошибка при пересылке ответа от поддержки: {e}")

# Функция для проверки, является ли сообщение от бота
def _is_bot_message(message: Message) -> bool:
    """Проверяет, отправлено ли сообщение ботом"""
    return message.from_user and message.from_user.is_bot

# Дополнительный обработчик для команды поддержки (если нужно очистить кэш)
@callback_router.message(lambda message: message.chat.id == SUPPORT_CHAT_ID and message.text and message.text.startswith("/clear_cache"))
async def clear_support_cache(message: Message):
    global support_messages
    support_messages.clear()
    await message.answer("Кэш служебных сообщений очищен.")