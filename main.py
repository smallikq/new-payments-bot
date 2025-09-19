import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import API_TOKEN
from core.database import init_database
from services.alerts.scheduler import schedule_auto_reset
from services.alerts import emergency
from userbot.client import init_userbot
from utils.logger import logger

# Импорт всех обработчиков
from bot.handlers.commands import setup_command_handlers
from bot.handlers.callbacks import setup_callback_handlers
from bot.handlers.messages import handle_private_text_message
from bot.handlers.media import setup_media_handlers
from bot.handlers.settings import setup_settings_handlers
from bot.middleware.auth import is_admin

# Глобальные переменные для graceful shutdown
bot_instance = None
dp_instance = None
userbot_instance = None


async def shutdown(signal_type=None):
    """Корректное завершение работы бота"""
    logger.info(f"🛑 Получен сигнал остановки: {signal_type}")

    try:
        # Остановка тревог
        if hasattr(emergency, 'force_stop_all_alerts'):
            await emergency.force_stop_all_alerts()

        # Остановка userbot
        if userbot_instance:
            await userbot_instance.disconnect()
            logger.info("✅ Userbot отключен")

        # Остановка polling
        if dp_instance and bot_instance:
            await dp_instance.stop_polling()
            await bot_instance.session.close()
            logger.info("✅ Bot отключен")

    except Exception as e:
        logger.error(f"❌ Ошибка при завершении: {e}")

    logger.info("👋 Payments Bot остановлен")


async def main():
    """Основная функция запуска бота"""
    global bot_instance, dp_instance, userbot_instance

    try:
        logger.info("=" * 50)
        logger.info("🚀 Запуск Payments Bot v2.0...")
        logger.info("=" * 50)

        # Инициализация БД
        logger.info("🔧 Инициализация базы данных...")
        init_database()

        # Инициализация aiogram-бота с настройками по умолчанию
        logger.info("🤖 Инициализация Telegram бота...")
        bot_instance = Bot(
            token=API_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        dp_instance = Dispatcher(storage=MemoryStorage())

        # Передаём bot в emergency для рассылки
        emergency.bot = bot_instance

        # === Регистрация всех хендлеров ===
        logger.info("📝 Регистрация обработчиков...")

        # 1. Команды (должны быть первыми)
        setup_command_handlers(dp_instance)

        # 2. Callback хендлеры (кнопки)
        setup_callback_handlers(dp_instance)

        # 3. Settings хендлеры (FSM)
        setup_settings_handlers(dp_instance)

        # 4. Media хендлеры (фото, документы, и т.д.)
        setup_media_handlers(dp_instance)

        # 5. Текстовые сообщения (должны быть в конце, чтобы не перехватывали команды)
        dp_instance.message.register(
            handle_private_text_message,
            lambda m: (
                    m.chat.type == "private" and
                    is_admin(m.from_user.id) and
                    m.text and
                    not m.text.startswith('/') and
                    not m.photo and
                    not m.document and
                    not m.voice and
                    not m.video and
                    not m.sticker
            )
        )

        logger.info("✅ Все хендлеры зарегистрированы")

        # === Запуск компонентов ===

        # Запуск userbot с обработчиками
        logger.info("📱 Инициализация userbot...")
        try:
            userbot_instance = await init_userbot()
            if userbot_instance:
                # Регистрируем обработчики userbot
                from userbot.handlers import setup_userbot_handlers
                setup_userbot_handlers(userbot_instance)

                # Запускаем userbot в фоне
                asyncio.create_task(userbot_instance.run_until_disconnected())
                logger.info("✅ Userbot запущен с обработчиками")
            else:
                logger.warning("⚠️ Userbot не инициализирован (проверьте API_ID/API_HASH)")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска userbot: {e}")

        # Запуск планировщика автосброса
        logger.info("⏰ Запуск планировщика автосброса...")
        try:
            asyncio.create_task(schedule_auto_reset())
            logger.info("✅ Планировщик запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")

        # Проверка начального состояния тревог
        logger.info("🚨 Проверка состояния тревог...")
        try:
            from services.alerts.emergency import check_emergency_conditions
            await check_emergency_conditions()
            logger.info("✅ Система тревог проверена")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки тревог: {e}")

        # Отправка уведомления о запуске админу
        try:
            from core.config import ADMIN_CHAT_ID
            await bot_instance.send_message(
                ADMIN_CHAT_ID,
                "🎉 <b>Payments Bot v2.0 запущен!</b>\n\n"
                "✅ Все системы активны\n"
                "📡 Готов к приему команд\n\n"
                "Используйте /start для начала работы",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о запуске: {e}")

        # Финальный статус
        logger.info("=" * 50)
        logger.info("🎉 Все компоненты инициализированы!")
        logger.info("📡 Бот готов к приему сообщений...")
        logger.info("=" * 50)

        # Запуск бота
        await dp_instance.start_polling(bot_instance, skip_updates=True)

    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        raise
    finally:
        await shutdown("main_exit")


def signal_handler(sig, frame):
    """Обработчик системных сигналов"""
    logger.info(f"Получен сигнал {sig}")
    asyncio.create_task(shutdown(sig))
    sys.exit(0)


if __name__ == "__main__":
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Запуск с обработкой ошибок
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
        sys.exit(1)