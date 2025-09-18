import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import API_TOKEN
from core.database import init_database
from services.alerts.scheduler import schedule_auto_reset
from services.alerts import emergency
from userbot.client import init_userbot
from userbot import handlers as userbot_handlers  # чтобы зарегистрировались обработчики

from bot.handlers.commands import handle_start_private
from bot.handlers.callbacks import (
    handle_balance_callback, handle_settings_callback,
    handle_help_callback, handle_status_callback
)
from bot.handlers.messages import handle_private_text_message
from bot.handlers.media import handle_check_private
from bot.handlers.settings import (
    handle_time_input, handle_checks_limit_input,
    handle_balance_limit_input, handle_alert_rate_input
)
from bot.states import SettingsStates
from bot.middleware.auth import is_admin


async def main():
    # 📌 Инициализация БД
    init_database()

    # 📌 Инициализация aiogram-бота
    bot = Bot(token=API_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    # передаём bot в emergency, чтобы рассылка работала
    emergency.bot = bot

    # === Хэндлеры ===

    # Команды
    dp.message.register(handle_start_private, Command("start"))

    # Callback кнопки
    dp.callback_query.register(handle_balance_callback, lambda c: c.data == "balance")
    dp.callback_query.register(handle_settings_callback, lambda c: c.data == "settings")
    dp.callback_query.register(handle_help_callback, lambda c: c.data == "help")
    dp.callback_query.register(handle_status_callback, lambda c: c.data == "status")

    # Сообщения (текст)
    dp.message.register(handle_private_text_message, lambda m: is_admin(m.from_user.id) and m.text)

    # Фото/документы (чеки)
    dp.message.register(lambda m: handle_check_private(m, bot),
                        lambda m: is_admin(m.from_user.id) and (m.photo or m.document))

    # FSM ввод настроек
    dp.message.register(handle_time_input, SettingsStates.waiting_for_time)
    dp.message.register(handle_checks_limit_input, SettingsStates.waiting_for_checks_limit)
    dp.message.register(handle_balance_limit_input, SettingsStates.waiting_for_balance_limit)
    dp.message.register(handle_alert_rate_input, SettingsStates.waiting_for_alert_rate)

    # 📌 Запускаем userbot (Telethon)
    userbot = await init_userbot()
    if userbot:
        asyncio.create_task(userbot.run_until_disconnected())

    # 📌 Планировщик автосброса
    asyncio.create_task(schedule_auto_reset())

    # 📌 Запуск aiogram
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("❌ Бот остановлен")
