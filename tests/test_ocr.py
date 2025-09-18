import pytest
from services.ocr.extractors import normalize_text_for_amounts, is_likely_payment_amount

def test_normalize_text_for_amounts():
    text = "1 000 200,50 грн"
    normalized = normalize_text_for_amounts(text)
    assert "1000200,50" not in normalized  # пробелы между цифрами убраны правильно
    assert "200,50" in normalized or "200.50" in normalized

def test_is_likely_payment_amount_true():
    text = "Оплата товара 250 грн"
    start, end = text.find("250"), text.find("250") + 3
    assert is_likely_payment_amount(250, text, start, end) is True

def test_is_likely_payment_amount_false():
    text = "Комиссия 50 грн"
    start, end = text.find("50"), text.find("50") + 2
    assert is_likely_payment_amount(50, text, start, end) is False
