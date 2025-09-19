from datetime import datetime
import pytz
from core.database import get_balance, withdrawals_without_check, get_settings_safe, get_statistics
from services.alerts.emergency import emergency_task


def format_balance_message():
    """Форматирует сообщение с балансом"""
    incoming, checks, max_balance = get_balance()
    balance = incoming - checks

    # Эмодзи статуса баланса
    if balance > 1000:
        status_emoji = "🟢"
        status_text = "Отличный"
    elif balance >= 0:
        status_emoji = "✅"
        status_text = "Положительный"
    elif balance >= -500:
        status_emoji = "⚠️"
        status_text = "Низкий"
    else:
        status_emoji = "🔴"
        status_text = "Критический"

    # Прогресс-бар для баланса
    def create_progress_bar(value, max_val, length=10):
        if max_val <= 0:
            return "▱" * length
        filled = int((value / max_val) * length) if value > 0 else 0
        return "▰" * filled + "▱" * (length - filled)

    balance_bar = create_progress_bar(max(0, balance), max(max_balance, 1000))

    return f"""
🏦 <b>ФИНАНСОВЫЙ БАЛАНС</b>
{'═' * 30}

💵 Пополнения: <code>{incoming:,.2f} ₴</code>
🧾 Расходы: <code>{checks:,.2f} ₴</code>
📊 Выводов без чеков: <code>{withdrawals_without_check}</code>

{status_emoji} <b>Баланс: {balance:,.2f} ₴</b>
{balance_bar}
📈 Статус: <b>{status_text}</b>
🎯 Максимум за период: <code>{max_balance:,.2f} ₴</code>

<i>Обновлено: {datetime.now(pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S')}</i>
"""


def format_statistics_message():
    """Форматирует подробную статистику"""
    stats = get_statistics()

    # Процентные показатели
    efficiency = (stats['checks'] / max(stats['incoming'], 1)) * 100 if stats['incoming'] > 0 else 0
    balance_ratio = (stats['balance'] / max(stats['max_balance'], 1)) * 100 if stats['max_balance'] > 0 else 0

    # Эмодзи для эффективности
    if efficiency > 90:
        eff_emoji = "🔴"
    elif efficiency > 70:
        eff_emoji = "⚠️"
    elif efficiency > 50:
        eff_emoji = "🟡"
    else:
        eff_emoji = "🟢"

    return f"""
📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>
{'═' * 30}

💰 <b>Обороты:</b>
├ Пополнений: <code>{stats['income_count']}</code> на <code>{stats['incoming']:,.2f} ₴</code>
├ Чеков: <code>{stats['check_count']}</code> на <code>{stats['checks']:,.2f} ₴</code>
└ Выводов: <code>{stats['withdrawal_count']}</code>

📈 <b>Показатели:</b>
├ Текущий баланс: <code>{stats['balance']:,.2f} ₴</code>
├ Максимальный: <code>{stats['max_balance']:,.2f} ₴</code>
├ Средний чек: <code>{stats['avg_check']:,.2f} ₴</code>
└ Незакрытых выводов: <code>{stats['withdrawals_without_check']}</code>

{eff_emoji} <b>Эффективность расходов:</b> {efficiency:.1f}%
📊 <b>Использование лимита:</b> {balance_ratio:.1f}%

<i>Период активен с момента последнего сброса</i>
"""


def format_settings_info():
    """Форматирует информацию о настройках"""
    auto_reset_time, critical_checks, critical_balance, alert_rate, emergency_enabled = get_settings_safe()

    enabled_status = "🟢 Включена" if emergency_enabled else "🔴 Отключена"
    reset_time_display = f"🕐 {auto_reset_time}" if auto_reset_time else "⚠️ Не задано"

    # Статус тревоги
    if emergency_task and not emergency_task.done():
        alert_status = "🚨 Активна"
        alert_color = "🔴"
    elif emergency_enabled:
        alert_status = "😴 Спит"
        alert_color = "🟡"
    else:
        alert_status = "❌ Отключена"
        alert_color = "⚫"

    return f"""
⚙️ <b>КОНФИГУРАЦИЯ СИСТЕМЫ</b>
{'═' * 30}

⏰ <b>Автосброс:</b> {reset_time_display}
{alert_color} <b>Система тревог:</b> {enabled_status}
└ Статус: {alert_status}

🚨 <b>Пороги срабатывания:</b>
├ Выводов подряд: <code>{critical_checks}</code>
└ Критический баланс: <code>{critical_balance:,.2f} ₴</code>

📢 <b>Уведомления:</b> <code>{alert_rate}</code> сообщ./мин

<i>Настройки сохраняются между перезапусками</i>
"""


def format_help_message():
    """Справочная информация"""
    return """
🤖 <b>РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ</b>
{'═' * 30}

📥 <b>Автоматическое распознавание:</b>
• Пополнения из банковских уведомлений
• Выводы и переводы (отрицательные суммы)
• OCR чеков из изображений

🧾 <b>Добавление чеков:</b>
Отправьте фото квитанции боту в личные сообщения.
Система автоматически распознает сумму.

🚨 <b>Система тревог:</b>
Активируется при достижении критических условий:
• Много выводов без подтверждающих чеков
• Превышение лимита баланса

⚙️ <b>Дополнительно:</b>
• Статистика в реальном времени
• Автосброс данных по расписанию  
• Экспорт данных для анализа

💡 <b>Совет:</b> Для лучшего распознавания отправляйте четкие фото чеков с хорошо видимыми суммами.
"""


def format_system_status():
    """Статус системы"""
    incoming, checks, _ = get_balance()
    balance = incoming - checks
    _, _, _, _, emergency_enabled = get_settings_safe()

    # Статус компонентов
    components = []

    # База данных
    try:
        from core.database import get_balance
        get_balance()
        components.append("🟢 База данных: Работает")
    except:
        components.append("🔴 База данных: Ошибка")

    # Система тревог
    if emergency_enabled:
        if emergency_task and not emergency_task.done():
            components.append("🚨 Тревоги: Активны")
        else:
            components.append("🟡 Тревоги: Готовы")
    else:
        components.append("⚫ Тревоги: Отключены")

    # Userbot (если доступен)
    try:
        from userbot.client import userbot
        if userbot and userbot.is_connected():
            components.append("🟢 Userbot: Подключен")
        else:
            components.append("🔴 Userbot: Отключен")
    except:
        components.append("⚠️ Userbot: Недоступен")

    # OCR система
    try:
        from services.ocr.processor import rapid_ocr
        if rapid_ocr:
            components.append("🟢 OCR: Готов")
        else:
            components.append("🔴 OCR: Ошибка")
    except:
        components.append("⚠️ OCR: Недоступен")

    status_text = "\n".join(f"├ {comp}" if i < len(components) - 1 else f"└ {comp}"
                            for i, comp in enumerate(components))

    uptime = datetime.now(pytz.timezone('Europe/Kiev')).strftime('%Y-%m-%d %H:%M:%S')

    return f"""
🛠️ <b>СТАТУС СИСТЕМЫ</b>
{'═' * 30}

💰 <b>Текущий баланс:</b> <code>{balance:,.2f} ₴</code>

🔧 <b>Компоненты:</b>
{status_text}

⏱️ <b>Время работы:</b> {uptime} (Киев)
🖥️ <b>Версия:</b> Payments Bot v2.0

<i>Система мониторинга финансов активна</i>
"""


def format_export_message(export_type: str, data: str):
    """Форматирует сообщение с экспортированными данными"""
    export_types = {
        'stats': 'Статистика',
        'history': 'История транзакций',
        'screenshots': 'Информация о чеках',
        'settings': 'Настройки системы'
    }

    title = export_types.get(export_type, 'Данные')
    timestamp = datetime.now(pytz.timezone('Europe/Kiev')).strftime('%Y-%m-%d %H:%M:%S')

    return f"""
📋 <b>ЭКСПОРТ: {title.upper()}</b>
{'═' * 30}

<pre>{data}</pre>

📅 <b>Создано:</b> {timestamp}
💾 <b>Формат:</b> Текстовый
📊 <b>Источник:</b> Payments Bot

<i>Данные актуальны на момент экспорта</i>
"""


def format_reset_confirmation():
    """Сообщение подтверждения сброса"""
    stats = get_statistics()

    return f"""
⚠️ <b>ПОДТВЕРЖДЕНИЕ СБРОСА</b>
{'═' * 30}

Вы собираетесь удалить ВСЕ данные:

💰 Баланс: <code>{stats['balance']:,.2f} ₴</code>
📊 Пополнений: <code>{stats['income_count']}</code>
🧾 Чеков: <code>{stats['check_count']}</code>
📝 Транзакций: <code>{stats['income_count'] + stats['check_count'] + stats['withdrawal_count']}</code>

<b>⚡ ВНИМАНИЕ:</b>
• Все финансовые данные будут потеряны
• История транзакций удалится навсегда
• Статистика обнулится
• Действие НЕОБРАТИМО

Продолжить?
"""


def format_test_alert():
    """Тестовое сообщение тревоги"""
    return f"""
🧪 <b>ТЕСТОВОЕ УВЕДОМЛЕНИЕ</b>
{'═' * 30}

Это проверка системы тревог.

📡 Отправлено: {datetime.now(pytz.timezone('Europe/Kiev')).strftime('%H:%M:%S')}
🎯 Статус: Система работает корректно

<i>Если вы видите это сообщение, уведомления настроены правильно.</i>
"""