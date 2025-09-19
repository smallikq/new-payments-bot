from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher

from bot.ui.messages import (
    format_balance_message, format_statistics_message, format_settings_info,
    format_help_message, format_system_status, format_export_message,
    format_reset_confirmation, format_test_alert
)
from bot.ui.keyboards import (
    create_main_menu, create_settings_menu, create_emergency_settings_menu,
    create_reset_confirmation, create_back_to_main, create_time_quick_set,
    create_limits_quick_set, create_balance_limits_quick_set,
    create_alert_rate_quick_set, create_export_menu
)
from bot.states import SettingsStates
from bot.middleware.auth import is_admin
from core.database import update_setting, reset_all_data, get_statistics, get_settings_safe
from services.alerts.emergency import stop_emergency_alerts, check_emergency_conditions
from utils.logger import logger


async def handle_balance_callback(callback: CallbackQuery):
    """Показать текущий баланс"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            format_balance_message(),
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        await callback.answer("💰 Баланс обновлен")
    except Exception as e:
        logger.error(f"Ошибка показа баланса: {e}")
        await callback.answer("❌ Ошибка загрузки данных", show_alert=True)


async def handle_statistics_callback(callback: CallbackQuery):
    """Показать детальную статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            format_statistics_message(),
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer("📊 Статистика загружена")
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)


async def handle_settings_callback(callback: CallbackQuery):
    """Показать меню настроек"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            format_settings_info(),
            parse_mode="HTML",
            reply_markup=create_settings_menu()
        )
        await callback.answer("⚙️ Настройки")
    except Exception as e:
        logger.error(f"Ошибка показа настроек: {e}")
        await callback.answer("❌ Ошибка загрузки настроек", show_alert=True)


async def handle_help_callback(callback: CallbackQuery):
    """Показать справку"""
    try:
        await callback.message.edit_text(
            format_help_message(),
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer("📖 Справка")
    except Exception as e:
        logger.error(f"Ошибка показа справки: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def handle_status_callback(callback: CallbackQuery):
    """Показать статус системы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            format_system_status(),
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer("🛠️ Статус системы")
    except Exception as e:
        logger.error(f"Ошибка показа статуса: {e}")
        await callback.answer("❌ Ошибка загрузки статуса", show_alert=True)


async def handle_toggle_emergency(callback: CallbackQuery):
    """Переключить систему тревог"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        _, _, _, _, current_state = get_settings_safe()
        new_state = not current_state

        update_setting("emergency_enabled", int(new_state))

        if not new_state:
            await stop_emergency_alerts()
            status_text = "🔴 Тревога ОТКЛЮЧЕНА"
        else:
            status_text = "🟢 Тревога ВКЛЮЧЕНА"
            # Проверяем условия после включения
            await check_emergency_conditions()

        await callback.message.edit_text(
            f"🚨 <b>СИСТЕМА ТРЕВОГ</b>\n\n{status_text}\n\nВернуться в главное меню?",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer(status_text)

    except Exception as e:
        logger.error(f"Ошибка переключения тревог: {e}")
        await callback.answer("❌ Ошибка переключения", show_alert=True)


async def handle_reset_confirm_callback(callback: CallbackQuery):
    """Показать подтверждение сброса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            format_reset_confirmation(),
            parse_mode="HTML",
            reply_markup=create_reset_confirmation()
        )
        await callback.answer("⚠️ Подтвердите сброс")
    except Exception as e:
        logger.error(f"Ошибка подтверждения сброса: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def handle_confirm_reset(callback: CallbackQuery):
    """Выполнить сброс данных"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        reset_all_data()
        await stop_emergency_alerts()

        await callback.message.edit_text(
            "✅ <b>СБРОС ВЫПОЛНЕН</b>\n\n"
            "Все данные удалены:\n"
            "• Баланс обнулен\n"
            "• История очищена\n"
            "• Тревоги остановлены\n\n"
            "Система готова к работе.",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer("🔄 Данные сброшены")
        logger.info("✅ Выполнен ручной сброс данных")

    except Exception as e:
        logger.error(f"Ошибка сброса: {e}")
        await callback.answer("❌ Ошибка сброса", show_alert=True)


async def handle_back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    try:
        welcome_text = f"🤖 <b>Payments Bot</b>\n\nДобро пожаловать, {callback.from_user.first_name}!"

        await callback.message.edit_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        await callback.answer("🏠 Главное меню")
    except Exception as e:
        logger.error(f"Ошибка возврата в меню: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# === Настройки времени ===

async def handle_set_time_callback(callback: CallbackQuery):
    """Меню установки времени автосброса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        current_time, _, _, _, _ = get_settings_safe()
        current_text = f"Текущее время: <code>{current_time or 'не задано'}</code>"

        await callback.message.edit_text(
            f"⏰ <b>ВРЕМЯ АВТОСБРОСА</b>\n\n{current_text}\n\nВыберите время или введите вручную:",
            parse_mode="HTML",
            reply_markup=create_time_quick_set()
        )
        await callback.answer("⏰ Настройка времени")
    except Exception as e:
        logger.error(f"Ошибка настройки времени: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def handle_quick_time(callback: CallbackQuery):
    """Быстрая установка времени"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        time_value = callback.data.split("_")[-1]  # извлекаем время из callback_data
        update_setting("auto_reset_time", time_value)

        await callback.message.edit_text(
            f"✅ <b>ВРЕМЯ ОБНОВЛЕНО</b>\n\n⏰ Автосброс: <code>{time_value}</code>\n\nВремя по Киеву",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer(f"⏰ Время установлено: {time_value}")

    except Exception as e:
        logger.error(f"Ошибка установки времени: {e}")
        await callback.answer("❌ Ошибка установки", show_alert=True)


async def handle_manual_time_input(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод времени"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_for_time)
    await callback.message.edit_text(
        "⏰ <b>ВВОД ВРЕМЕНИ</b>\n\n"
        "Введите время в формате <code>ЧЧ:ММ</code>\n"
        "Примеры: <code>06:00</code>, <code>18:30</code>, <code>23:59</code>\n\n"
        "Время указывается по Киеву.",
        parse_mode="HTML",
        reply_markup=create_back_to_main()
    )
    await callback.answer("✏️ Введите время")


# === Emergency settings ===

async def handle_emergency_settings(callback: CallbackQuery):
    """Меню настроек тревог"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        _, critical_checks, critical_balance, _, emergency_enabled = get_settings_safe()
        status = "🟢 Включена" if emergency_enabled else "🔴 Отключена"

        await callback.message.edit_text(
            f"🚨 <b>НАСТРОЙКИ ТРЕВОГ</b>\n\n"
            f"Система: {status}\n"
            f"Лимит выводов: <code>{critical_checks}</code>\n"
            f"Критический баланс: <code>{critical_balance:.2f} ₴</code>",
            parse_mode="HTML",
            reply_markup=create_emergency_settings_menu()
        )
        await callback.answer("🚨 Настройки тревог")
    except Exception as e:
        logger.error(f"Ошибка настроек тревог: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


async def handle_test_alerts(callback: CallbackQuery):
    """Тест системы уведомлений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        from core.config import ALERT_CHAT_IDS
        from services.alerts.emergency import bot

        if bot:
            test_message = format_test_alert()
            for chat_id in ALERT_CHAT_IDS:
                try:
                    await bot.send_message(chat_id, test_message, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Не удалось отправить тест в чат {chat_id}: {e}")

        await callback.answer("🧪 Тестовые уведомления отправлены")

    except Exception as e:
        logger.error(f"Ошибка теста уведомлений: {e}")
        await callback.answer("❌ Ошибка теста", show_alert=True)


# === Export menu ===

async def handle_export_data(callback: CallbackQuery):
    """Меню экспорта данных"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "📋 <b>ЭКСПОРТ ДАННЫХ</b>\n\nВыберите тип данных для экспорта:",
            parse_mode="HTML",
            reply_markup=create_export_menu()
        )
        await callback.answer("📋 Экспорт данных")
    except Exception as e:
        logger.error(f"Ошибка меню экспорта: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


def setup_callback_handlers(dp: Dispatcher):
    """Регистрирует все callback handlers"""

    # Основные кнопки меню
    dp.callback_query.register(handle_balance_callback, lambda c: c.data == "balance")
    dp.callback_query.register(handle_statistics_callback, lambda c: c.data == "stats")
    dp.callback_query.register(handle_settings_callback, lambda c: c.data == "settings")
    dp.callback_query.register(handle_help_callback, lambda c: c.data == "help")
    dp.callback_query.register(handle_status_callback, lambda c: c.data == "status")
    dp.callback_query.register(handle_back_to_main, lambda c: c.data == "back_to_main")

    # Управление системой
    dp.callback_query.register(handle_toggle_emergency, lambda c: c.data == "toggle_emergency")
    dp.callback_query.register(handle_reset_confirm_callback, lambda c: c.data == "reset_confirm")
    dp.callback_query.register(handle_confirm_reset, lambda c: c.data == "confirm_reset")

    # Настройки времени
    dp.callback_query.register(handle_set_time_callback, lambda c: c.data == "set_time")
    dp.callback_query.register(handle_quick_time, lambda c: c.data.startswith("quick_time_"))
    dp.callback_query.register(handle_manual_time_input, lambda c: c.data == "manual_time_input")

    # Настройки тревог
    dp.callback_query.register(handle_emergency_settings, lambda c: c.data == "emergency_settings")
    dp.callback_query.register(handle_test_alerts, lambda c: c.data == "test_alerts")

    # Экспорт
    dp.callback_query.register(handle_export_data, lambda c: c.data == "export_data")

    # Игнорирование пустых callbacks
    dp.callback_query.register(lambda c: c.answer(), lambda c: c.data == "noop")