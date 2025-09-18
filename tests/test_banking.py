import pytest
from services.banking.parser import extract_bank_payment

@pytest.mark.parametrize("text,expected", [
    ("Пополнение карты +300,00₴ MONO Direct", 300.00),
    ("Списание -150 грн", -150.0),
    ("Зачисление: 200.50 UAH", 200.50),
    ("Перевод: 100 грн на карту", 100.0),
    ("Ошибка: нет суммы", None),
])
def test_extract_bank_payment(text, expected):
    result = extract_bank_payment(text)
    if expected is None:
        assert result is None
    else:
        assert abs(result - expected) < 0.01
