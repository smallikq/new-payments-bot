from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_settings_safe, get_balance, withdrawals_without_check


def create_main_menu():
    """Главное меню с современным дизайном и эмодзи-индикаторами"""
    _, _, _, _, emergency_enabled = get_settings_safe()
    incoming, checks, _ = get_balance()
    balance = incoming - checks

    # Динамические эмодзи для статуса
    emergency_emoji = "🟢" if emergency_enabled else "🔴"
    emergency_text = f"{emergency_emoji} Тревога {'ON' if emergency_enabled else 'OFF'}"

    # Индикатор баланса
    if balance > 1000:
        balance_indicator = "💚"
    elif balance >= 0:
        balance_indicator = "💛"
    else:
        balance_indicator = "💔"

    # Индикатор выводов
    withdrawal_indicator = "🔴" if withdrawals_without_check >= 3 else "🟢"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{balance_indicator} Баланс ({balance:,.0f} ₴)",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                text=f"📊 Статистика",
                callback_data="stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="settings"
            ),
            InlineKeyboardButton(
                text=f"{withdrawal_indicator} Система",
                callback_data="status"
            )
        ],
        [
            InlineKeyboardButton(
                text=emergency_text,
                callback_data="toggle_emergency"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Сброс данных",
                callback_data="reset_confirm"
            ),
            InlineKeyboardButton(
                text="📋 Экспорт",
                callback_data="export_data"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="help"
            ),
            InlineKeyboardButton(
                text="🔔 Тест тревог",
                callback_data="test_alerts"
            )
        ]
    ])


def create_settings_menu():
    """Меню настроек с группировкой по категориям"""
    auto_reset_time, critical_checks, critical_balance, alert_rate, emergency_enabled = get_settings_safe()

    # Индикаторы настроек
    time_indicator = "✅" if auto_reset_time else "⚠️"
    emergency_indicator = "🟢" if emergency_enabled else "🔴"

    return InlineKeyboardMarkup(inline_keyboard=[
        # Категория: Время
        [
            InlineKeyboardButton(
                text=f"{time_indicator} ⏰ Автосброс: {auto_reset_time or 'не задано'}",
                callback_data="set_time"
            )
        ],
        # Категория: Тревоги
        [
            InlineKeyboardButton(
                text=f"{emergency_indicator} 🚨 Система тревог",
                callback_data="emergency_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📋 Лимит: {critical_checks} выводов",
                callback_data="set_checks_limit"
            ),
            InlineKeyboardButton(
                text=f"💸 Порог: {critical_balance:.0f} ₴",
                callback_data="set_balance_limit"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📢 Частота: {alert_rate}/мин",
                callback_data="set_alert_rate"
            )
        ],
        # Дополнительно
        [
            InlineKeyboardButton(
                text="📤 Экспорт настроек",
                callback_data="export_settings"
            ),
            InlineKeyboardButton(
                text="📥 Импорт настроек",
                callback_data="import_settings"
            )
        ],
        # Навигация
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_main"
            )
        ]
    ])


def create_emergency_settings_menu():
    """Детальное меню настроек тревог"""
    _, critical_checks, critical_balance, alert_rate, emergency_enabled = get_settings_safe()

    status = "🟢 Активна" if emergency_enabled else "🔴 Отключена"

    # Прогресс-бары для визуализации
    checks_bar = "█" * min(critical_checks, 10) + "░" * (10 - min(critical_checks, 10))
    rate_bar = "█" * min(alert_rate // 2, 10) + "░" * (10 - min(alert_rate // 2, 10))

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🚨 Система: {status}",
                callback_data="toggle_emergency"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📊 Выводов: {critical_checks}",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text=checks_bar,
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="➖",
                callback_data=f"quick_limit_{max(1, critical_checks - 1)}"
            ),
            InlineKeyboardButton(
                text="Изменить лимит",
                callback_data="set_checks_limit"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"quick_limit_{min(20, critical_checks + 1)}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"💰 Баланс: {critical_balance:.0f} ₴",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="-100",
                callback_data=f"quick_balance_{critical_balance - 100}"
            ),
            InlineKeyboardButton(
                text="Изменить порог",
                callback_data="set_balance_limit"
            ),
            InlineKeyboardButton(
                text="+100",
                callback_data=f"quick_balance_{critical_balance + 100}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📢 Частота: {alert_rate}/мин",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text=rate_bar,
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="🐌 Медленно",
                callback_data="quick_rate_1"
            ),
            InlineKeyboardButton(
                text="🚶 Нормально",
                callback_data="quick_rate_5"
            ),
            InlineKeyboardButton(
                text="⚡ Быстро",
                callback_data="quick_rate_10"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Тест уведомлений",
                callback_data="test_alerts"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ К настройкам",
                callback_data="settings"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="back_to_main"
            )
        ]
    ])


def create_reset_confirmation():
    """Подтверждение сброса с визуальным предупреждением"""
    from core.database import get_statistics
    stats = get_statistics()

    # Показываем что будет удалено
    data_size = stats['income_count'] + stats['check_count'] + stats['withdrawal_count']

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📊 Будет удалено {data_size} записей",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚠️ ПОДТВЕРЖДАЮ СБРОС ⚠️",
                callback_data="confirm_reset"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="back_to_main"
            )
        ]
    ])


def create_back_to_main():
    """Кнопка возврата с контекстной информацией"""
    incoming, checks, _ = get_balance()
    balance = incoming - checks

    balance_emoji = "💚" if balance >= 0 else "💔"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🏠 Главное меню {balance_emoji} ({balance:,.0f} ₴)",
                callback_data="back_to_main"
            )
        ]
    ])


def create_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str):
    """Улучшенная пагинация с номерами страниц"""
    keyboard = []

    # Первая строка - быстрая навигация
    if total_pages > 5:
        quick_nav = []
        if current_page > 1:
            quick_nav.append(InlineKeyboardButton(text="⏮️", callback_data=f"{callback_prefix}_page_1"))
        if current_page > 10:
            quick_nav.append(
                InlineKeyboardButton(text="⏪", callback_data=f"{callback_prefix}_page_{current_page - 10}"))
        if current_page < total_pages - 9:
            quick_nav.append(
                InlineKeyboardButton(text="⏩", callback_data=f"{callback_prefix}_page_{current_page + 10}"))
        if current_page < total_pages:
            quick_nav.append(InlineKeyboardButton(text="⏭️", callback_data=f"{callback_prefix}_page_{total_pages}"))

        if quick_nav:
            keyboard.append(quick_nav)

    # Основная навигация
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"{callback_prefix}_page_{current_page - 1}"))

    # Показываем соседние страницы
    page_range = []
    for i in range(max(1, current_page - 2), min(total_pages + 1, current_page + 3)):
        if i == current_page:
            page_range.append(InlineKeyboardButton(text=f"·{i}·", callback_data="noop"))
        else:
            page_range.append(InlineKeyboardButton(text=str(i), callback_data=f"{callback_prefix}_page_{i}"))

    nav_buttons.extend(page_range)

    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"{callback_prefix}_page_{current_page + 1}"))

    keyboard.append(nav_buttons)

    # Информация о позиции
    keyboard.append([
        InlineKeyboardButton(
            text=f"📄 Страница {current_page} из {total_pages}",
            callback_data="noop"
        )
    ])

    # Кнопка возврата
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_time_quick_set():
    """Быстрые пресеты времени с визуальными подсказками"""
    current_time, _, _, _, _ = get_settings_safe()

    # Визуальные индикаторы времени суток
    times = [
        ("🌅 Раннее утро", "06:00"),
        ("☀️ Утро", "09:00"),
        ("🌞 День", "12:00"),
        ("🌇 Вечер", "18:00"),
        ("🌃 Ночь", "00:00"),
        ("🌙 Поздняя ночь", "03:00")
    ]

    keyboard = []
    for i in range(0, len(times), 2):
        row = []
        for j in range(i, min(i + 2, len(times))):
            label, time = times[j]
            is_current = current_time == time
            btn_text = f"{'✅ ' if is_current else ''}{label} ({time})"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"quick_time_{time}"))
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_time_input")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_limits_quick_set():
    """Пресеты лимитов с описаниями"""
    current_limit, _, _, _, _ = get_settings_safe()
    current_limit = current_limit or 5

    presets = [
        (3, "🟢 Мягкий", "Минимальный контроль"),
        (5, "🟡 Обычный", "Стандартный уровень"),
        (10, "🟠 Строгий", "Повышенный контроль"),
        (15, "🔴 Очень строгий", "Максимальный контроль")
    ]

    keyboard = []
    for value, level, desc in presets:
        is_current = current_limit == value
        btn_text = f"{'✅ ' if is_current else ''}{level}: {value} ({desc})"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"quick_limit_{value}")
        ])

    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести число", callback_data="manual_limit_input")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_balance_limits_quick_set():
    """Пресеты критического баланса с визуализацией"""
    _, _, current_balance, _, _ = get_settings_safe()

    presets = [
        (-100, "💚", "Минимальный риск"),
        (-500, "💛", "Умеренный риск"),
        (-1000, "🟠", "Повышенный риск"),
        (-2000, "🔴", "Высокий риск"),
        (-5000, "💀", "Критический риск")
    ]

    keyboard = []
    for value, emoji, desc in presets:
        is_current = abs(current_balance - value) < 0.01
        btn_text = f"{'✅ ' if is_current else ''}{emoji} {value} ₴ - {desc}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"quick_balance_{value}")
        ])

    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести сумму", callback_data="manual_balance_input")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_alert_rate_quick_set():
    """Пресеты частоты уведомлений с визуальным отображением скорости"""
    _, _, _, current_rate, _ = get_settings_safe()

    presets = [
        (1, "🐌", "Очень медленно", "1 сообщение в минуту"),
        (3, "🚶", "Медленно", "Каждые 20 секунд"),
        (5, "🚴", "Нормально", "Каждые 12 секунд"),
        (10, "🏃", "Быстро", "Каждые 6 секунд"),
        (20, "⚡", "Очень быстро", "Каждые 3 секунды"),
        (60, "🚀", "Максимум", "Каждую секунду")
    ]

    keyboard = []
    for rate, emoji, speed, desc in presets:
        is_current = current_rate == rate
        btn_text = f"{'✅ ' if is_current else ''}{emoji} {speed}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"quick_rate_{rate}"),
            InlineKeyboardButton(text=desc, callback_data="noop")
        ])

    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести число", callback_data="manual_rate_input")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_export_menu():
    """Меню экспорта с иконками форматов"""
    from core.database import get_statistics
    stats = get_statistics()

    # Показываем объем данных
    total_records = stats['income_count'] + stats['check_count'] + stats['withdrawal_count']

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"💾 Всего записей: {total_records}",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(text="📊 Статистика (.txt)", callback_data="export_stats"),
            InlineKeyboardButton(text="📝 История (.csv)", callback_data="export_history")
        ],
        [
            InlineKeyboardButton(text="🖼️ Чеки (.json)", callback_data="export_screenshots"),
            InlineKeyboardButton(text="⚙️ Настройки (.json)", callback_data="export_settings")
        ],
        [
            InlineKeyboardButton(text="📦 Полный бэкап (.zip)", callback_data="export_full_backup")
        ],
        [
            InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ])


def create_check_processing_menu():
    """Меню обработки чека с опциями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Повторить распознавание", callback_data="retry_ocr"),
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_amount_input")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ])


def create_set_checks_limit_menu():
    """Меню установки лимита выводов"""
    _, current_limit, _, _, _ = get_settings_safe()

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📊 Текущий лимит: {current_limit} выводов",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(text="1", callback_data="quick_limit_1"),
            InlineKeyboardButton(text="3", callback_data="quick_limit_3"),
            InlineKeyboardButton(text="5", callback_data="quick_limit_5"),
            InlineKeyboardButton(text="7", callback_data="quick_limit_7"),
            InlineKeyboardButton(text="10", callback_data="quick_limit_10")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_limit_input")
        ],
        [
            InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
        ]
    ])


def create_set_balance_limit_menu():
    """Меню установки критического баланса"""
    _, _, current_balance, _, _ = get_settings_safe()

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"💰 Текущий порог: {current_balance:.0f} ₴",
                callback_data="noop"
            )
        ],
        [
            InlineKeyboardButton(text="0", callback_data="quick_balance_0"),
            InlineKeyboardButton(text="-500", callback_data="quick_balance_-500"),
            InlineKeyboardButton(text="-1000", callback_data="quick_balance_-1000")
        ],
        [
            InlineKeyboardButton(text="-2000", callback_data="quick_balance_-2000"),
            InlineKeyboardButton(text="-5000", callback_data="quick_balance_-5000"),
            InlineKeyboardButton(text="-10000", callback_data="quick_balance_-10000")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_balance_input")
        ],
        [
            InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
        ]
    ])