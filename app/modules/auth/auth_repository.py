from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.auth_models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    if not user_id:
        return None
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    username = (username or "").strip()
    if not username:
        return None
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def get_user_by_employee_id(db: Session, employee_id: str) -> User | None:
    if not employee_id:
        return None
    statement = select(User).where(User.employee_id == employee_id)
    return db.scalar(statement)


def add_user(db: Session, user: User) -> User:
    db.add(user)
    return user


def update_user_password(user: User, password_hash: str) -> None:
    user.password_hash = password_hash


def update_user_status(user: User, is_active: bool) -> None:
    user.is_active = is_active
