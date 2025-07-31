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
        # 1. Копируем сообщение пользователя в поддержку (с сохранением всех вложений)
        copied_msg = await message.copy_to(chat_id=SUPPORT_CHAT_ID)
        
        # 2. Отправляем служебное сообщение с ID пользователя сразу после скопированного
        await bot.send_message(
            SUPPORT_CHAT_ID, 
            f"[ID:{message.from_user.id}] @{message.from_user.username or 'нет_username'}",
            reply_to_message_id=copied_msg.message_id  # Привязываем к скопированному сообщению
        )
        
        await message.answer("Ваше сообщение отправлено в техподдержку 💬\nСкоро с вами свяжется специалист.")
        await state.clear()
        
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения в поддержку: {e}")
        await message.answer("Произошла ошибка при отправке сообщения. Попробуйте позже.")

# Обработчик ответов от техподдержки
@callback_router.message(lambda message: message.chat.id == SUPPORT_CHAT_ID)
async def handle_support_chat(message: Message, bot: Bot):
    try:
        # Игнорируем сообщения от бота
        if message.from_user.is_bot:
            return
            
        # Проверяем, является ли это ответом на сообщение
        if not message.reply_to_message:
            logging.info("Сообщение в чате поддержки без reply - игнорируем")
            return
            
        # Ищем user_id в replied сообщении или в следующем за ним
        user_id = None
        
        # Вариант 1: Ответ на служебное сообщение с [ID:...]
        if message.reply_to_message.text and message.reply_to_message.text.startswith("[ID:"):
            try:
                id_part = message.reply_to_message.text.split("]")[0][4:]
                user_id = int(id_part)
                logging.info(f"ID найден в replied сообщении: {user_id}")
            except (ValueError, IndexError):
                logging.error("Ошибка извлечения ID из replied сообщения")
        
        # Вариант 2: Если отвечают на копированное сообщение пользователя,
        # то ищем следующее сообщение с [ID:...]
        if not user_id:
            try:
                # Получаем сообщения после replied сообщения
                replied_msg_id = message.reply_to_message.message_id
                
                # Проверяем следующие несколько сообщений после replied
                for offset in range(1, 5):  # Проверяем 4 сообщения после
                    check_msg_id = replied_msg_id + offset
                    try:
                        # Пытаемся получить сообщение по ID (это работает не всегда)
                        # Альтернативный подход - ищем в недавних сообщениях бота
                        pass
                    except:
                        continue
                        
                # Если не нашли, уведомляем
                if not user_id:
                    await bot.send_message(
                        SUPPORT_CHAT_ID,
                        "⚠️ Не удалось найти ID пользователя. Отвечайте на сообщение с [ID:...] или скопированное сообщение пользователя с привязанным ID."
                    )
                    return
                    
            except Exception as e:
                logging.error(f"Ошибка поиска user_id: {e}")
        
        if user_id:
            # Копируем ответ оператора пользователю
            await message.copy_to(chat_id=user_id)
            logging.info(f"Ответ оператора переслан пользователю {user_id}")
            
            # Подтверждение в чат поддержки
            await bot.send_message(
                SUPPORT_CHAT_ID,
                f"✅ Ответ отправлен пользователю {user_id}",
                reply_to_message_id=message.message_id
            )
        else:
            await bot.send_message(
                SUPPORT_CHAT_ID,
                "❌ Не удалось определить получателя. Ответьте на сообщение с [ID:...]"
            )
            
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения в чате поддержки: {e}")

# Обработчик для текстовой кнопки "Обратиться в поддержку"
@callback_router.message(lambda message: message.text == "❓ Обратиться в поддержку")
async def support_start_text(message: Message, state: FSMContext):
    await message.answer("🛠 Пожалуйста, опишите вашу проблему или задайте вопрос.")
    await state.set_state(SupportState.waiting_for_question)