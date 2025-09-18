import sqlite3
import asyncio
import pytz
from datetime import datetime
from core.config import DATABASE_PATH
from utils.logger import logger
from services.alerts.emergency import check_emergency_conditions

# Глобальные переменные
withdrawals_without_check = 0
last_income_time = None

def init_database():
    """Создает и инициализирует структуру базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS totals (
            id INTEGER PRIMARY KEY,
            incoming REAL DEFAULT 0,
            checks REAL DEFAULT 0,
            max_balance REAL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_text TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            auto_reset_time TEXT,
            critical_checks_count INTEGER DEFAULT 5,
            critical_balance_amount REAL DEFAULT -1000.0,
            alert_messages_per_minute INTEGER DEFAULT 5,
            emergency_enabled INTEGER DEFAULT 1
        )
    """)

    cursor.execute("INSERT OR IGNORE INTO totals (id, incoming, checks) VALUES (1, 0, 0)")
    cursor.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


def get_balance():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT incoming, checks, max_balance FROM totals WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row if row else (0.0, 0.0, 0.0)


def update_max_balance():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT incoming, checks, max_balance FROM totals WHERE id=1")
    incoming, checks, max_balance = cur.fetchone()
    balance = incoming - checks

    if balance > max_balance:
        cur.execute("UPDATE totals SET max_balance=? WHERE id=1", (balance,))
        logger.info(f"Обновлен максимальный баланс: {balance:.2f} UAH")

    conn.commit()
    conn.close()


def add_income(amount: float):
    global last_income_time
    if amount <= 0:
        logger.warning(f"Игнорируем неположительное значение ({amount}) как пополнение")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE totals SET incoming = incoming + ? WHERE id=1", (amount,))
    cur.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("income", amount))
    conn.commit()
    conn.close()

    last_income_time = datetime.now(pytz.timezone("Europe/Kiev"))
    logger.info(f"Добавлено пополнение: {amount} UAH")

    update_max_balance()
    asyncio.create_task(check_emergency_conditions())


def add_withdrawal(amount: float):
    global withdrawals_without_check
    if amount >= 0:
        logger.warning(f"Игнорируем неположительное значение ({amount}) как вывод")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("withdrawal", amount))
    conn.commit()
    conn.close()

    withdrawals_without_check += 1
    logger.info(f"Зафиксирован вывод: {amount} UAH. Незакрытых выводов: {withdrawals_without_check}")

    update_max_balance()
    asyncio.create_task(check_emergency_conditions())


def add_check(amount: float):
    global withdrawals_without_check
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE totals SET checks = checks + ? WHERE id=1", (amount,))
    cur.execute("INSERT INTO transaction_history(type, amount) VALUES(?, ?)", ("check", amount))
    conn.commit()
    conn.close()

    if withdrawals_without_check > 0:
        withdrawals_without_check -= 1
        logger.info(f"Добавлен чек: {amount} UAH. Осталось незакрытых: {withdrawals_without_check}")

    update_max_balance()
    asyncio.create_task(check_emergency_conditions())
