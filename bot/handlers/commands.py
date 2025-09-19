from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
# Добавляем импорт для новых callback обработчиков
from bot.ui.keyboards import (
    create_main_menu, create_settings_menu, create_emergency_settings_menu,
    create_reset_confirmation, create_back_to_main, create_time_quick_set,
    create_limits_quick_set, create_balance_limits_quick_set,
    create_alert_rate_quick_set, create_export_menu, create_set_checks_limit_menu,
    create_set_balance_limit_menu
)
from bot.ui.messages import format_balance_message, format_help_message
from bot.middleware.auth import is_admin
from utils.logger import logger


async def handle_start_command(message: Message):
    """Обработчик команды /start"""
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ <b>Доступ запрещен</b>\n\n"
            "У вас нет прав для использования этого бота.\n"
            "Обратитесь к администратору.",
            parse_mode="HTML"
        )
        logger.warning(f"Попытка доступа от {message.from_user.id} (@{message.from_user.username})")
        return

    welcome_text = f"""
🚀 <b>Payments Bot v2.0</b>

Добро пожаловать, {message.from_user.first_name}! 👋

🎯 <b>Возможности бота:</b>
├ 💰 Автоматическое отслеживание пополнений
├ 🧾 OCR распознавание чеков
├ 🚨 Система экстренных уведомлений
├ 📊 Детальная статистика и аналитика
├ ⏰ Автосброс по расписанию
└ 📤 Экспорт данных

💡 <b>Быстрые действия:</b>
• Отправьте фото чека для распознавания
• Используйте меню ниже для управления

<i>Система мониторинга активна и готова к работе!</i>
"""

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")


async def handle_balance_command(message: Message):
    """Обработчик команды /balance"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    await message.answer(
        format_balance_message(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )


async def handle_help_command(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        format_help_message(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )


async def handle_stats_command(message: Message):
    """Обработчик команды /stats"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from bot.ui.messages import format_statistics_message
    await message.answer(
        format_statistics_message(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )


async def handle_reset_command(message: Message):
    """Обработчик команды /reset"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from bot.ui.keyboards import create_reset_confirmation
    from bot.ui.messages import format_reset_confirmation

    await message.answer(
        format_reset_confirmation(),
        parse_mode="HTML",
        reply_markup=create_reset_confirmation()
    )


async def handle_settings_command(message: Message):
    """Обработчик команды /settings"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from bot.ui.messages import format_settings_info
    from bot.ui.keyboards import create_settings_menu

    await message.answer(
        format_settings_info(),
        parse_mode="HTML",
        reply_markup=create_settings_menu()
    )


async def handle_status_command(message: Message):
    """Обработчик команды /status"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from bot.ui.messages import format_system_status

    await message.answer(
        format_system_status(),
        parse_mode="HTML",
        reply_markup=create_main_menu()
    )


async def handle_emergency_command(message: Message):
    """Обработчик команды /emergency - быстрое управление тревогами"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from services.alerts.emergency import get_emergency_status
    status = get_emergency_status()

    if status['active']:
        from bot.ui.keyboards import create_alert_control_menu
        text = f"""
🚨 <b>ТРЕВОГА АКТИВНА!</b>

📊 Отправлено уведомлений: {status['alert_count']}
⏰ Последнее: {status['last_alert'] or 'нет данных'}

Выберите действие:
"""
        keyboard = create_alert_control_menu()
    else:
        text = "🟢 Система тревог в режиме ожидания"
        keyboard = create_main_menu()

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


async def handle_export_command(message: Message):
    """Обработчик команды /export - быстрый экспорт"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    from bot.ui.keyboards import create_export_menu

    await message.answer(
        "📤 <b>Быстрый экспорт данных</b>\n\nВыберите формат:",
        parse_mode="HTML",
        reply_markup=create_export_menu()
    )


def setup_command_handlers(dp: Dispatcher):
    """Регистрирует все обработчики команд"""
    dp.message.register(handle_start_command, Command(commands=["start"]))
    dp.message.register(handle_balance_command, Command(commands=["balance", "b"]))
    dp.message.register(handle_help_command, Command(commands=["help", "h"]))
    dp.message.register(handle_stats_command, Command(commands=["stats", "s"]))
    dp.message.register(handle_reset_command, Command(commands=["reset"]))
    dp.message.register(handle_settings_command, Command(commands=["settings", "set"]))
    dp.message.register(handle_status_command, Command(commands=["status"]))
    dp.message.register(handle_emergency_command, Command(commands=["emergency", "alert"]))
    dp.message.register(handle_export_command, Command(commands=["export"]))

    logger.info("✅ Обработчики команд зарегистрированы")