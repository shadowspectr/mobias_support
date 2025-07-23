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
    support_chat_id = -1002837608854 # Замените на реальный ID чата с поддержкой
    user_question = message.text

    # Пересылаем вопрос в чат техподдержки
    await message.bot.send_message(support_chat_id, f"Новый вопрос от пользователя:\n\n{user_question}")

    await message.answer("Ваш вопрос был отправлен в техподдержку. Ожидайте ответа.")
    await state.clear()  # Сбрасываем состояние


# Обработчик пересылки ответа из техподдержки пользователю
@callback_router.message()
async def forward_support_response(message: types.Message):
    if message.chat.id == -1002837608854:  # Замените на ID чата техподдержки
        # Здесь предполагается, что в первом сообщении будет ID пользователя
        parts = message.text.split(":", 1)
        if len(parts) == 2:
            user_id = int(parts[0])
            support_answer = parts[1].strip()

            # Отправляем ответ пользователю
            await message.bot.send_message(user_id, f"Ответ от техподдержки:\n\n{support_answer}")
