import re
from utils.logger import logger

def extract_bank_payment(text: str):
    """
    Извлекает сумму платежа из банковских уведомлений.
    Примеры:
    - "+300,00₴ MONO Direct"
    - "-150 грн"
    - "Зачисление: 200.50 UAH"
    """
    patterns = [
        r"[-+]?\d+[.,]\d+\s*₴",
        r"[-+]?\d+\s*₴",
        r"[-+]?\d+[.,]\d+\s*(?:грн|UAH)",
        r"[-+]?\d+\s*(?:грн|UAH)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                amount_str = re.search(r"[-+]?\d+[.,]?\d*", match.group(0)).group(0)
                value = float(amount_str.replace(",", "."))
                logger.info(f"Извлечена сумма {value} UAH из текста: {match.group(0)}")
                return value
            except Exception as e:
                logger.error(f"Ошибка при извлечении суммы: {e}")
                continue

    logger.debug(f"Сумма не найдена в тексте: {text[:50]}...")
    return None
