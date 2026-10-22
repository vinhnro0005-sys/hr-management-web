"""Đường dẫn import chung; dùng model Employee duy nhất trong module."""

from app.modules.employee.employee_models import Employee

__all__ = ["Employee"]
