import sqlite3
import asyncio
import pytz
from datetime import datetime
from typing import Tuple, Optional
from core.config import DATABASE_PATH
from utils.logger import logger

# Глобальные переменные для отслеживания состояния
withdrawals_without_check = 0
last_income_time = None


def init_database():
    """Создает и инициализирует структуру базы данных"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Таблица истории транзакций
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS transaction_history
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           type
                           TEXT
                           NOT
                           NULL
                           CHECK (
                           type
                           IN
                       (
                           'income',
                           'withdrawal',
                           'check'
                       )),
                           amount REAL NOT NULL,
                           description TEXT DEFAULT '',
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                           )
                       """)

        # Таблица общих балансов
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS totals
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           CHECK
                       (
                           id =
                           1
                       ),
                           incoming REAL DEFAULT 0 CHECK
                       (
                           incoming
                           >=
                           0
                       ),
                           checks REAL DEFAULT 0 CHECK
                       (
                           checks
                           >=
                           0
                       ),
                           max_balance REAL DEFAULT 0
                           )
                       """)

        # Таблица скриншотов чеков
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS screenshots
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           file_id
                           TEXT
                           NOT
                           NULL,
                           amount
                           REAL
                           DEFAULT
                           0,
                           raw_text
                           TEXT
                           DEFAULT
                           '',
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       """)

        # Таблица настроек
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS settings
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           CHECK
                       (
                           id =
                           1
                       ),
                           auto_reset_time TEXT DEFAULT NULL,
                           critical_checks_count INTEGER DEFAULT 5 CHECK
                       (
                           critical_checks_count >
                           0
                       ),
                           critical_balance_amount REAL DEFAULT -1000.0,
                           alert_messages_per_minute INTEGER DEFAULT 5 CHECK
                       (
                           alert_messages_per_minute >
                           0
                       ),
                           emergency_enabled INTEGER DEFAULT 1 CHECK
                       (
                           emergency_enabled
                           IN
                       (
                           0,
                           1
                       ))
                           )
                       """)

        # Инициализация данных по умолчанию
        cursor.execute("INSERT OR IGNORE INTO totals (id, incoming, checks, max_balance) VALUES (1, 0, 0, 0)")
        cursor.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


def get_balance() -> Tuple[float, float, float]:
    """Получает текущий баланс (пополнения, расходы, максимальный баланс)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT incoming, checks, max_balance FROM totals WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        return row if row else (0.0, 0.0, 0.0)
    except Exception as e:
        logger.error(f"❌ Ошибка получения баланса: {e}")
        return (0.0, 0.0, 0.0)


def get_settings_safe() -> Tuple[Optional[str], int, float, int, bool]:
    """Безопасно получает настройки с значениями по умолчанию"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT auto_reset_time,
                              critical_checks_count,
                              critical_balance_amount,
                              alert_messages_per_minute,
                              emergency_enabled
                       FROM settings
                       WHERE id = 1
                       """)
        row = cursor.fetchone()
        conn.close()

        if row:
            auto_reset_time, critical_checks, critical_balance, alert_rate, emergency_enabled = row
            return auto_reset_time, critical_checks, critical_balance, alert_rate, bool(emergency_enabled)
        else:
            return None, 5, -1000.0, 5, True
    except Exception as e:
        logger.error(f"❌ Ошибка получения настроек: {e}")
        return None, 5, -1000.0, 5, True


def update_setting(key: str, value):
    """Обновляет настройку в БД"""
    try:
        valid_keys = {
            'auto_reset_time': 'TEXT',
            'critical_checks_count': 'INTEGER',
            'critical_balance_amount': 'REAL',
            'alert_messages_per_minute': 'INTEGER',
            'emergency_enabled': 'INTEGER'
        }

        if key not in valid_keys:
            logger.warning(f"⚠️ Некорректный ключ настройки: {key}")
            return False

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE settings SET {key} = ? WHERE id=1", (value,))
        conn.commit()
        conn.close()
        logger.info(f"✅ Обновлена настройка {key} = {value}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка обновления настройки {key}: {e}")
        return False


def update_max_balance():
    """Обновляет максимальный баланс если текущий больше"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT incoming, checks, max_balance FROM totals WHERE id=1")
        row = cursor.fetchone()

        if not row:
            conn.close()
            return

        incoming, checks, max_balance = row
        current_balance = incoming - checks

        if current_balance > max_balance:
            cursor.execute("UPDATE totals SET max_balance=? WHERE id=1", (current_balance,))
            conn.commit()
            logger.info(f"📈 Обновлен максимальный баланс: {current_balance:.2f} UAH")

        conn.close()
    except Exception as e:
        logger.error(f"❌ Ошибка обновления максимального баланса: {e}")


def add_income(amount: float):
    """Добавляет пополнение"""
    global last_income_time

    if amount <= 0:
        logger.warning(f"⚠️ Игнорируем неположительную сумму пополнения: {amount}")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE totals SET incoming = incoming + ? WHERE id=1", (amount,))
        cursor.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("income", amount))
        conn.commit()
        conn.close()

        last_income_time = datetime.now(pytz.timezone("Europe/Kiev"))
        logger.info(f"💰 Добавлено пополнение: {amount:.2f} UAH")

        update_max_balance()

        # Проверяем условия тревоги
        from services.alerts.emergency import check_emergency_conditions
        asyncio.create_task(check_emergency_conditions())

    except Exception as e:
        logger.error(f"❌ Ошибка добавления пополнения: {e}")


def add_withdrawal(amount: float):
    """Добавляет вывод (отрицательная сумма)"""
    global withdrawals_without_check

    if amount >= 0:
        logger.warning(f"⚠️ Игнорируем неотрицательную сумму вывода: {amount}")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("withdrawal", amount))
        conn.commit()
        conn.close()

        withdrawals_without_check += 1
        logger.info(f"💸 Зафиксирован вывод: {amount:.2f} UAH. Незакрытых выводов: {withdrawals_without_check}")

        # Проверяем условия тревоги
        from services.alerts.emergency import check_emergency_conditions
        asyncio.create_task(check_emergency_conditions())

    except Exception as e:
        logger.error(f"❌ Ошибка добавления вывода: {e}")


def add_check(amount: float):
    """Добавляет чек (расход)"""
    global withdrawals_without_check

    if amount <= 0:
        logger.warning(f"⚠️ Игнорируем неположительную сумму чека: {amount}")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE totals SET checks = checks + ? WHERE id=1", (amount,))
        cursor.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("check", amount))
        conn.commit()
        conn.close()

        # Закрываем один вывод если есть незакрытые
        if withdrawals_without_check > 0:
            withdrawals_without_check -= 1

        logger.info(f"🧾 Добавлен чек: {amount:.2f} UAH. Незакрытых выводов: {withdrawals_without_check}")

        update_max_balance()

        # Проверяем условия тревоги
        from services.alerts.emergency import check_emergency_conditions
        asyncio.create_task(check_emergency_conditions())

    except Exception as e:
        logger.error(f"❌ Ошибка добавления чека: {e}")


def save_check_screenshot(file_id: str, amount: float, raw_text: str):
    """Сохраняет информацию о скриншоте чека"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO screenshots(file_id, amount, raw_text) VALUES(?, ?, ?)",
            (file_id, amount, raw_text)
        )
        conn.commit()
        conn.close()
        logger.debug(f"💾 Сохранен скриншот: {file_id}, сумма: {amount}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения скриншота: {e}")


def reset_all_data():
    """Полный сброс всех данных периода"""
    global withdrawals_without_check

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Обнуляем балансы
        cursor.execute("UPDATE totals SET incoming=0, checks=0, max_balance=0 WHERE id=1")

        # Очищаем историю
        cursor.execute("DELETE FROM transaction_history")
        cursor.execute("DELETE FROM screenshots")

        conn.commit()
        conn.close()

        # Сбрасываем счетчик
        withdrawals_without_check = 0

        logger.info("🔄 Выполнен полный сброс данных")

    except Exception as e:
        logger.error(f"❌ Ошибка сброса данных: {e}")


def get_statistics() -> dict:
    """Получает статистику текущего периода"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Основные суммы
        cursor.execute("SELECT incoming, checks, max_balance FROM totals WHERE id=1")
        incoming, checks, max_balance = cursor.fetchone() or (0, 0, 0)

        # Количество транзакций
        cursor.execute("SELECT COUNT(*) FROM transaction_history WHERE type='income'")
        income_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM transaction_history WHERE type='check'")
        check_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM transaction_history WHERE type='withdrawal'")
        withdrawal_count = cursor.fetchone()[0]

        # Средний чек
        cursor.execute("SELECT AVG(amount) FROM transaction_history WHERE type='check' AND amount > 0")
        avg_check = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'balance': incoming - checks,
            'incoming': incoming,
            'checks': checks,
            'max_balance': max_balance,
            'income_count': income_count,
            'check_count': check_count,
            'withdrawal_count': withdrawal_count,
            'avg_check': avg_check,
            'withdrawals_without_check': withdrawals_without_check
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return {
            'balance': 0, 'incoming': 0, 'checks': 0, 'max_balance': 0,
            'income_count': 0, 'check_count': 0, 'withdrawal_count': 0,
            'avg_check': 0, 'withdrawals_without_check': 0
        }