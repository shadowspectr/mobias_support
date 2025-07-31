from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# Состояния для машины состояний
class SupportState(StatesGroup):
    waiting_for_question = State()  # Состояние ожидания вопроса


callback_router = Router()


# Обработчик для кнопки "Обратиться в поддержку"
@callback_router.callback_query(lambda c: c.data == "support")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🛠 Пожалуйста, опишите вашу проблему или задайте вопрос.")
    await state.set_state(SupportState.waiting_for_question)  # Устанавливаем состояние ожидания вопроса


# Обработчик получения вопроса
@callback_router.message(SupportState.waiting_for_question)
async def receive_support_question(message: types.Message, state: FSMContext):
    support_chat_id = -1002837608854

    # Пересылаем сообщение с вложением
    forwarded = await message.forward(support_chat_id)
    await message.bot.send_message(support_chat_id, f"[ID:{message.from_user.id}]")
    
    await message.answer("Ваше сообщение отправлено в поддержку 💬")
    await state.clear()


# Обработчик пересылки ответа из техподдержки пользователю
@callback_router.message()
async def forward_support_response(message: types.Message):
    if message.chat.id == -1002837608854:
        try:
            # Получаем user_id из предыдущих сообщений
            history = await message.bot.get_chat_history(-1002837608854, limit=5)
            user_id = None
            for msg in history:
                if msg.text and msg.text.startswith("[ID:"):
                    try:
                        user_id = int(msg.text.strip()[4:-1])
                        break
                    except:
                        continue

            if user_id:
                await message.copy_to(chat_id=user_id)
        except Exception as e:
            print(f"Ошибка при пересылке вложения пользователю: {e}")

