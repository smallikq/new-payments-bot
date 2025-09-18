import os
import sqlite3
import tempfile
import pytest
from core import database

@pytest.fixture
def temp_db(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    monkeypatch.setattr(database, "DATABASE_PATH", db_path)
    database.init_database()
    yield db_path
    os.remove(db_path)

def test_add_income_and_balance(temp_db):
    database.add_income(500)
    incoming, checks, max_balance = database.get_balance()
    assert incoming >= 500
    assert checks == 0
    assert max_balance >= 500

def test_add_withdrawal_and_check(temp_db):
    database.add_withdrawal(-100)
    database.add_check(100)
    incoming, checks, max_balance = database.get_balance()
    assert checks >= 100
