from aiogram.fsm.state import State, StatesGroup

class SettingsStates(StatesGroup):
    """Состояния для ввода различных настроек"""
    waiting_for_time = State()
    waiting_for_checks_limit = State()
    waiting_for_balance_limit = State()
    waiting_for_alert_rate = State()
