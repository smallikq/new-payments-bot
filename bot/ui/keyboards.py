from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database import get_settings_safe


def create_main_menu():
    """Главное меню с современным дизайном"""
    _, _, _, _, emergency_enabled = get_settings_safe()
    emergency_emoji = "🟢" if emergency_enabled else "🔴"
    emergency_text = f"{emergency_emoji} Тревога {'ON' if emergency_enabled else 'OFF'}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="🛠️ Система", callback_data="status")
        ],
        [
            InlineKeyboardButton(text=emergency_text, callback_data="toggle_emergency")
        ],
        [
            InlineKeyboardButton(text="🔄 Сброс данных", callback_data="reset_confirm"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])


def create_settings_menu():
    """Меню настроек"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Время автосброса", callback_data="set_time"),
            InlineKeyboardButton(text="🚨 Настройки тревог", callback_data="emergency_settings")
        ],
        [
            InlineKeyboardButton(text="📢 Частота уведомлений", callback_data="set_alert_rate"),
            InlineKeyboardButton(text="📋 Экспорт данных", callback_data="export_data")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ])


def create_emergency_settings_menu():
    """Меню настроек тревог"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Лимит выводов", callback_data="set_checks_limit"),
            InlineKeyboardButton(text="💸 Критический баланс", callback_data="set_balance_limit")
        ],
        [
            InlineKeyboardButton(text="🔄 Тест уведомлений", callback_data="test_alerts")
        ],
        [
            InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ])


def create_reset_confirmation():
    """Подтверждение сброса данных"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ ДА, СБРОСИТЬ ВСЕ", callback_data="confirm_reset")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_main")
        ]
    ])


def create_back_to_main():
    """Простая кнопка возврата в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])


def create_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str):
    """Создает клавиатуру с пагинацией"""
    keyboard = []

    # Кнопки навигации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"{callback_prefix}_page_{current_page - 1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop"))

    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"{callback_prefix}_page_{current_page + 1}"))

    keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_time_quick_set():
    """Быстрые кнопки для установки времени автосброса"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌅 06:00", callback_data="quick_time_06:00"),
            InlineKeyboardButton(text="🌇 18:00", callback_data="quick_time_18:00")
        ],
        [
            InlineKeyboardButton(text="🌃 00:00", callback_data="quick_time_00:00"),
            InlineKeyboardButton(text="🏁 23:59", callback_data="quick_time_23:59")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_time_input")
        ],
        [
            InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings")
        ]
    ])


def create_limits_quick_set():
    """Быстрые кнопки для лимитов"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="3️⃣", callback_data="quick_limit_3"),
            InlineKeyboardButton(text="5️⃣", callback_data="quick_limit_5"),
            InlineKeyboardButton(text="🔟", callback_data="quick_limit_10")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести число", callback_data="manual_limit_input")
        ],
        [
            InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
        ]
    ])


def create_balance_limits_quick_set():
    """Быстрые кнопки для критического баланса"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 -500", callback_data="quick_balance_-500"),
            InlineKeyboardButton(text="💰 -1000", callback_data="quick_balance_-1000")
        ],
        [
            InlineKeyboardButton(text="🚨 -2000", callback_data="quick_balance_-2000"),
            InlineKeyboardButton(text="💔 -5000", callback_data="quick_balance_-5000")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести сумму", callback_data="manual_balance_input")
        ],
        [
            InlineKeyboardButton(text="🚨 К тревогам", callback_data="emergency_settings")
        ]
    ])


def create_alert_rate_quick_set():
    """Быстрые кнопки для частоты уведомлений"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🐌 1/мин", callback_data="quick_rate_1"),
            InlineKeyboardButton(text="🚶 3/мин", callback_data="quick_rate_3")
        ],
        [
            InlineKeyboardButton(text="🏃 5/мин", callback_data="quick_rate_5"),
            InlineKeyboardButton(text="⚡ 10/мин", callback_data="quick_rate_10")
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести число", callback_data="manual_rate_input")
        ],
        [
            InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings")
        ]
    ])


def create_export_menu():
    """Меню экспорта данных"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Текущая статистика", callback_data="export_stats"),
            InlineKeyboardButton(text="📝 История транзакций", callback_data="export_history")
        ],
        [
            InlineKeyboardButton(text="🖼️ Все чеки (ID)", callback_data="export_screenshots"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="export_settings")
        ],
        [
            InlineKeyboardButton(text="⚙️ К настройкам", callback_data="settings")
        ]
    ])