import secrets

import bcrypt


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Mật khẩu không được vượt quá 72 byte")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    try:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def verify_csrf_token(session_token: str | None, form_token: str | None) -> bool:
    if not session_token or not form_token:
        return False
    try:
        return secrets.compare_digest(session_token, form_token)
    except Exception:
        return False


from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from app.core.config import settings

RESET_TOKEN_SALT = "hr-password-reset-salt"


def generate_password_reset_token(user_id: int, session_version: int) -> str:
    """Tạo token đặt lại mật khẩu an toàn có kèm phiên bản session."""
    serializer = URLSafeTimedSerializer(settings.session_secret_key, salt=RESET_TOKEN_SALT)
    return serializer.dumps({"user_id": user_id, "v": session_version})


def verify_password_reset_token(token: str, max_age: int = 900) -> dict | None:
    """Xác thực token đặt lại mật khẩu (mặc định hết hạn sau 15 phút = 900 giây)."""
    if not token:
        return None
    serializer = URLSafeTimedSerializer(settings.session_secret_key, salt=RESET_TOKEN_SALT)
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except (SignatureExpired, BadSignature, Exception):
        return None

