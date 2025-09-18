import re
from utils.logger import logger

def extract_bank_payment(text: str):
    """Извлекает сумму платежа из банковских уведомлений"""
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
                return float(amount_str.replace(",", "."))
            except Exception:
                continue
    return None


def normalize_text_for_amounts(text: str) -> str:
    """Нормализует текст для поиска денежных сумм"""
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace("\u00A0", " ").replace("\u202F", " ").replace("\u2009", " ")
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def is_likely_payment_amount(amount: float, text: str, start_pos: int, end_pos: int) -> bool:
    """Эвристики: является ли число суммой платежа"""
    if not (1 <= amount <= 50000):
        return False

    context_before = text[max(0, start_pos - 30):start_pos].lower()
    context_after = text[end_pos:end_pos + 30].lower()
    context = context_before + context_after

    if any(k in context for k in ['коміс', 'комис', 'fee']):
        return False
    if any(k in context for k in ['телефон', 'phone', 'тел', 'номер', '+38']):
        return False
    if any(k in context for k in ['карт', 'iban', 'рахун', 'card']):
        return False
    if any(k in context for k in ['дата', 'час', 'року']):
        return False

    return True
