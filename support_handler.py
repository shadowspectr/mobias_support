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
    support_chat_id = -1002837608854  # Замените на ваш ID

    try:
        # Пересылаем сообщение с вложением как есть
        await message.copy_to(chat_id=support_chat_id)

        # Отправляем системный идентификатор пользователя
        await message.bot.send_message(support_chat_id, f"[ID:{message.from_user.id}]")

        await message.answer("Ваше сообщение отправлено в техподдержку 💬\nСкоро с вами свяжется специалист.")
        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при отправке сообщения.")
        print(f"[Ошибка пересылки сообщения в поддержку] {e}")



# Обработчик пересылки ответа из техподдержки пользователю
@callback_router.message()
async def forward_support_response(message: types.Message):
    if message.chat.id == -1002837608854:
        try:
            # Ищем последний [ID:...] в истории
            history = await message.bot.get_chat_history(message.chat.id, limit=5)
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
            else:
                await message.answer("Не удалось определить ID пользователя для ответа.")
        except Exception as e:
            print(f"[Ошибка пересылки ответа от поддержки] {e}")


