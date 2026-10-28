import secrets

import bcrypt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def verify_csrf_token(session_token: str | None, form_token: str | None) -> bool:
    if not session_token or not form_token:
        return False
    return secrets.compare_digest(session_token, form_token)
