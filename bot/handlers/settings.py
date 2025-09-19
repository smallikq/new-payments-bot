from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
import re

from bot.states import SettingsStates
from bot.ui.keyboards import create_main_menu, create_back_to_main
from core.database import update_setting, get_statistics
from bot.middleware.auth import is_admin
from utils.logger import logger


# === Обработчики текстового ввода ===

async def handle_time_input(message: Message, state: FSMContext):
    """Обработка ввода времени автосброса"""
    if not is_admin(message.from_user.id):
        return

    time_text = message.text.strip()

    # Проверяем формат времени
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_text):
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Используйте формат <code>ЧЧ:ММ</code>\n"
            "Примеры: <code>06:00</code>, <code>18:30</code>, <code>23:59</code>",
            parse_mode="HTML"
        )
        return

    try:
        update_setting("auto_reset_time", time_text)
        await state.clear()

        await message.answer(
            f"✅ <b>ВРЕМЯ УСТАНОВЛЕНО</b>\n\n"
            f"⏰ Автосброс: <code>{time_text}</code> (Киев)\n\n"
            f"Система будет автоматически сбрасывать данные каждый день в указанное время.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        logger.info(f"Время автосброса установлено: {time_text}")

    except Exception as e:
        logger.error(f"Ошибка установки времени: {e}")
        await message.answer(
            "❌ <b>Ошибка сохранения</b>\n\nПопробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )


async def handle_checks_limit_input(message: Message, state: FSMContext):
    """Обработка ввода лимита выводов"""
    if not is_admin(message.from_user.id):
        return

    try:
        limit = int(message.text.strip())

        if limit < 1 or limit > 100:
            await message.answer(
                "❌ <b>Неверное значение!</b>\n\n"
                "Лимит должен быть от 1 до 100 выводов.",
                parse_mode="HTML"
            )
            return

        update_setting("critical_checks_count", limit)
        await state.clear()

        await message.answer(
            f"✅ <b>ЛИМИТ ОБНОВЛЕН</b>\n\n"
            f"📋 Критическое количество выводов: <code>{limit}</code>\n\n"
            f"Тревога будет активироваться при {limit} выводах подряд без чеков.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        logger.info(f"Лимит выводов установлен: {limit}")

    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите целое число от 1 до 100.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка установки лимита выводов: {e}")
        await message.answer(
            "❌ <b>Ошибка сохранения</b>\n\nПопробуйте еще раз.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )


async def handle_balance_limit_input(message: Message, state: FSMContext):
    """Обработка ввода критического баланса"""
    if not is_admin(message.from_user.id):
        return

    try:
        balance = float(message.text.strip().replace(',', '.'))

        if balance > 0:
            await message.answer(
                "⚠️ <b>Внимание!</b>\n\n"
                "Вы установили положительное значение критического баланса. "
                "Обычно используются отрицательные значения (например, -1000).\n\n"
                "Продолжить?",
                parse_mode="HTML"
            )
            # Можно добавить подтверждение, пока просто продолжаем

        update_setting("critical_balance_amount", balance)
        await state.clear()

        symbol = "+" if balance >= 0 else ""
        await message.answer(
            f"✅ <b>БАЛАНС ОБНОВЛЕН</b>\n\n"
            f"💸 Критический баланс: <code>{symbol}{balance:.2f} ₴</code>\n\n"
            f"Тревога будет активироваться при достижении этого значения.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        logger.info(f"Критический баланс установлен: {balance}")

    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите число (например: -1000, -500.50, 0).",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка установки критического баланса: {e}")
        await message.answer(
            "❌ <b>Ошибка сохранения</b>\n\nПопробуйте еще раз.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )


async def handle_alert_rate_input(message: Message, state: FSMContext):
    """Обработка ввода частоты уведомлений"""
    if not is_admin(message.from_user.id):
        return

    try:
        rate = int(message.text.strip())

        if rate < 1 or rate > 60:
            await message.answer(
                "❌ <b>Неверное значение!</b>\n\n"
                "Частота должна быть от 1 до 60 сообщений в минуту.",
                parse_mode="HTML"
            )
            return

        update_setting("alert_messages_per_minute", rate)
        await state.clear()

        interval = 60 / rate
        await message.answer(
            f"✅ <b>ЧАСТОТА ОБНОВЛЕНА</b>\n\n"
            f"📢 Уведомлений: <code>{rate}</code> в минуту\n"
            f"⏱️ Интервал: <code>{interval:.1f}</code> секунд\n\n"
            f"Тревожные сообщения будут отправляться с указанной частотой.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        logger.info(f"Частота уведомлений установлена: {rate}/мин")

    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Введите целое число от 1 до 60.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка установки частоты уведомлений: {e}")
        await message.answer(
            "❌ <b>Ошибка сохранения</b>\n\nПопробуйте еще раз.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )


# === Callback handlers для быстрых настроек ===

async def handle_quick_limits(callback: CallbackQuery):
    """Быстрая установка лимитов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        limit = int(callback.data.split("_")[-1])
        update_setting("critical_checks_count", limit)

        await callback.message.edit_text(
            f"✅ <b>ЛИМИТ УСТАНОВЛЕН</b>\n\n"
            f"📋 Критическое количество выводов: <code>{limit}</code>",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer(f"📋 Лимит: {limit} выводов")

    except Exception as e:
        logger.error(f"Ошибка быстрой установки лимита: {e}")
        await callback.answer("❌ Ошибка установки", show_alert=True)


async def handle_quick_balance(callback: CallbackQuery):
    """Быстрая установка критического баланса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        balance = float(callback.data.split("_")[-1])
        update_setting("critical_balance_amount", balance)

        await callback.message.edit_text(
            f"✅ <b>БАЛАНС УСТАНОВЛЕН</b>\n\n"
            f"💸 Критический баланс: <code>{balance:.0f} ₴</code>",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer(f"💸 Баланс: {balance:.0f} ₴")

    except Exception as e:
        logger.error(f"Ошибка быстрой установки баланса: {e}")
        await callback.answer("❌ Ошибка установки", show_alert=True)


async def handle_quick_rate(callback: CallbackQuery):
    """Быстрая установка частоты уведомлений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        rate = int(callback.data.split("_")[-1])
        update_setting("alert_messages_per_minute", rate)

        interval = 60 / rate
        await callback.message.edit_text(
            f"✅ <b>ЧАСТОТА УСТАНОВЛЕНА</b>\n\n"
            f"📢 Уведомлений: <code>{rate}</code>/мин\n"
            f"⏱️ Интервал: <code>{interval:.1f}</code> сек",
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer(f"📢 Частота: {rate}/мин")

    except Exception as e:
        logger.error(f"Ошибка быстрой установки частоты: {e}")
        await callback.answer("❌ Ошибка установки", show_alert=True)


# === Handlers для ручного ввода ===

async def handle_manual_limits_input(callback: CallbackQuery, state: FSMContext):
    """Переход к ручному вводу лимитов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_for_checks_limit)
    await callback.message.edit_text(
        "📋 <b>ЛИМИТ ВЫВОДОВ</b>\n\n"
        "Введите максимальное количество выводов подряд без чеков.\n\n"
        "Диапазон: <code>1-100</code>\n"
        "Рекомендуется: <code>3-10</code>",
        parse_mode="HTML",
        reply_markup=create_back_to_main()
    )
    await callback.answer("✏️ Введите лимит выводов")


async def handle_manual_balance_input(callback: CallbackQuery, state: FSMContext):
    """Переход к ручному вводу критического баланса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_for_balance_limit)
    await callback.message.edit_text(
        "💸 <b>КРИТИЧЕСКИЙ БАЛАНС</b>\n\n"
        "Введите значение баланса для активации тревоги.\n\n"
        "Примеры:\n"
        "• <code>-1000</code> - тревога при балансе ≥ -1000₴\n"
        "• <code>0</code> - тревога при положительном балансе\n"
        "• <code>5000</code> - тревога при балансе ≥ 5000₴",
        parse_mode="HTML",
        reply_markup=create_back_to_main()
    )
    await callback.answer("✏️ Введите критический баланс")


async def handle_manual_rate_input(callback: CallbackQuery, state: FSMContext):
    """Переход к ручному вводу частоты"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_for_alert_rate)
    await callback.message.edit_text(
        "📢 <b>ЧАСТОТА УВЕДОМЛЕНИЙ</b>\n\n"
        "Введите количество сообщений в минуту при активной тревоге.\n\n"
        "Диапазон: <code>1-60</code>\n"
        "Рекомендуется: <code>3-10</code>\n\n"
        "⚠️ Слишком высокая частота может привести к спаму!",
        parse_mode="HTML",
        reply_markup=create_back_to_main()
    )
    await callback.answer("✏️ Введите частоту уведомлений")


# === Обработчики экспорта данных ===

async def handle_export_stats(callback: CallbackQuery):
    """Экспорт статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        stats = get_statistics()

        export_data = f"""СТАТИСТИКА СИСТЕМЫ
{'=' * 40}
Баланс: {stats['balance']:.2f} ₴
Пополнений: {stats['income_count']} на {stats['incoming']:.2f} ₴
Расходов: {stats['check_count']} на {stats['checks']:.2f} ₴
Выводов: {stats['withdrawal_count']}
Максимальный баланс: {stats['max_balance']:.2f} ₴
Средний чек: {stats['avg_check']:.2f} ₴
Незакрытых выводов: {stats['withdrawals_without_check']}

Эффективность: {(stats['checks'] / max(stats['incoming'], 1) * 100):.1f}%
"""

        from bot.ui.messages import format_export_message
        message_text = format_export_message('stats', export_data)

        await callback.message.edit_text(
            message_text,
            parse_mode="HTML",
            reply_markup=create_back_to_main()
        )
        await callback.answer("📊 Статистика экспортирована")

    except Exception as e:
        logger.error(f"Ошибка экспорта статистики: {e}")
        await callback.answer("❌ Ошибка экспорта", show_alert=True)


def setup_settings_handlers(dp: Dispatcher):
    """Регистрирует все handlers для настроек"""

    # FSM text handlers
    dp.message.register(handle_time_input, SettingsStates.waiting_for_time)
    dp.message.register(handle_checks_limit_input, SettingsStates.waiting_for_checks_limit)
    dp.message.register(handle_balance_limit_input, SettingsStates.waiting_for_balance_limit)
    dp.message.register(handle_alert_rate_input, SettingsStates.waiting_for_alert_rate)

    # Quick setting callbacks
    dp.callback_query.register(handle_quick_limits, lambda c: c.data.startswith("quick_limit_"))
    dp.callback_query.register(handle_quick_balance, lambda c: c.data.startswith("quick_balance_"))
    dp.callback_query.register(handle_quick_rate, lambda c: c.data.startswith("quick_rate_"))

    # Manual input callbacks
    dp.callback_query.register(handle_manual_limits_input, lambda c: c.data == "manual_limit_input")
    dp.callback_query.register(handle_manual_balance_input, lambda c: c.data == "manual_balance_input")
    dp.callback_query.register(handle_manual_rate_input, lambda c: c.data == "manual_rate_input")

    # Alert rate settings
    dp.callback_query.register(
        lambda c, s=None: callback_with_quick_rate_menu(c),
        lambda c: c.data == "set_alert_rate"
    )

    # Export handlers
    dp.callback_query.register(handle_export_stats, lambda c: c.data == "export_stats")


async def callback_with_quick_rate_menu(callback: CallbackQuery):
    """Показать меню быстрой установки частоты"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    try:
        from core.database import get_settings_safe
        _, _, _, current_rate, _ = get_settings_safe()

        await callback.message.edit_text(
            f"📢 <b>ЧАСТОТА УВЕДОМЛЕНИЙ</b>\n\n"
            f"Текущая частота: <code>{current_rate}</code> сообщ./мин\n\n"
            f"Выберите новое значение или введите вручную:",
            parse_mode="HTML",
            reply_markup=create_alert_rate_quick_set()
        )
        await callback.answer("📢 Настройка частоты")
    except Exception as e:
        logger.error(f"Ошибка меню частоты: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# Импорт функции создания клавиатуры
from bot.ui.keyboards import create_alert_rate_quick_set