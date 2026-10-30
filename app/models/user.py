"""Đường dẫn import chung; dùng model User duy nhất trong module."""

from app.modules.auth.auth_models import User

__all__ = ["User"]
