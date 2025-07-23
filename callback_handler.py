from aiogram import Router, types
from aiogram.types import CallbackQuery
from keyboard import get_start_keyboard  # Импортируйте другие необходимые функции
from keyboard import get_app_keyboard
from keyboard import get_pay_keyboard
from keyboard import get_location_keyboard
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold


# Создаем роутер для callback query
callback_router = Router()

@callback_router.callback_query()
async def process_callback(callback: CallbackQuery):
    if callback.data == "get_product":
        app_links = [
            ("App Store", "https://apps.apple.com/us/app/%D0%BE%D0%B7%D0%BE%D0%BD-%D0%BE%D0%BD%D0%BB%D0%B0%D0%B9%D0%BD-%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BD%D0%B5%D1%82-%D0%BC%D0%B0%D0%B3%D0%B0%D0%B7%D0%B8%D0%BD/id407804998"),
            ("Google Play", "https://play.google.com/store/apps/details?id=ru.ozon.app.android"),
            ("AppGallery", "https://appgallery.huawei.com/#/app/C100847609"),
            ("RuStore", "https://apps.rustore.ru/app/ru.ozon.app.android")
        ]
        
        app_links_text = "\n".join(f"<a href='{link}'>{name}</a>" for name, link in app_links)
        
        await callback.message.answer(
            f"Чтобы начать пользоваться бесплатной доставкой, скачайте {hbold('приложение')}.\n\n"
            f"{app_links_text}",
            parse_mode="HTML"
        )

        instructions = [
            "Найдите пункт выдачи поблизости к вам, у нас для этого есть команда:",
            "📍  Найти пункт выдачи поблизости",
            "Добавьте понравившийся пункт выдачи в приложение Ozon, перейдя по предложенной ссылке",
            "Оформите заказ, дальше приложение само вам подскажет, когда стоит приходить за выбранным товаром!"
        ]

        await callback.message.answer(
            "\n\n".join(instructions),
            parse_mode="HTML",
            reply_markup=get_app_keyboard()
        )

    elif callback.data == "info":
        await callback.message.answer(
            "Выберите ваш способ оплаты:",
            parse_mode="HTML",
            reply_markup= get_pay_keyboard()
        )
    

    elif callback.data == "set_bank_card":
        await callback.message.answer(
            "<b>💸Привязать банковскую карту</b>\n" 
            "1. При оформлении заказа в разделе <b>Способ оплаты</b> выберите <b>Новой картой</b> и нажмите <b>Оплатить онлайн</b>.\n"
            "2. В открывшемся окне введите номер карты, срок действия карты и CVV/CVC код.\n" 
            "3. Нажмите розовую кнопку <b>Оплатить</b>.\n" 
            "4. Сохраните этот способ оплаты.\n",
            parse_mode="HTML"
        )
    
    elif callback.data == "set_sbp_card":
        await callback.message.answer(
            "<b>💸СБП</b>\n" 
            "1. При оформлении заказа в разделе <b>Способ оплаты</b> выберите <b>Система быстрых платежей</b> и нажмите <b>Оплатить онлайн</b>.\n"
            "2. Откройте мобильное приложение вашего банка и перейдите в раздел <b>Платежи</b> выберите <b>Оплатить по QR-коду</b>.\n" 
            "3. Отсканируйте QR-код и подтвердите оплату.\n" 
            "4. Сохраните этот способ оплаты.\n",
            parse_mode="HTML"
        )

    elif callback.data  == "set_ozon_bank_card":
        await callback.message.answer(
            "<b>💸Ozon Bank</b>\n" 
            "1. При оформлении заказа в разделе <b>Способ оплаты</b> выберите <b>Ozon карту</b> и нажмите <b>Оплатить онлайн</b>.\n"
            "2. Введите 4-х значный пароль от карты Ozon и нажмите <b>Оплатить онлайн</b>.\n"  
            "4. Сохраните этот способ оплаты.\n",
            parse_mode="HTML"
        )
    
    elif callback.data == "find_pickup":
        await callback.message.answer(
            "Пришлите своё текущее местоположение, чтобы увидеть пункты выдачи по близости!\n"
            "Убедитесь, что у вас включена функция 'Геолокации' на устройстве",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Отправить геопозицию", request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )


    else:
        await callback.answer("Неизвестная команда")
    
    # Не забудьте ответить на callback query, чтобы убрать "часики" на кнопке
    await callback.answer()

