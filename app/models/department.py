"""Đường dẫn import chung; dùng model Department duy nhất trong module."""

from app.modules.department.department_models import Department

__all__ = ["Department"]
