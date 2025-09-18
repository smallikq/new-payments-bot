from core.config import ADMIN_CHAT_ID

def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == ADMIN_CHAT_ID
