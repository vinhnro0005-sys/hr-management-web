from fastapi import Depends, HTTPException, Request

from app.database import SessionLocal
from app.models.employee import Employee
from app.modules.auth.auth_models import User
from app.modules.auth.auth_repository import get_user_by_id
from app.modules.auth.auth_service import EMPLOYEE_ACTIVE, ROLE_ADMIN, ROLE_EMPLOYEE

LOGIN_URL = "/login"


def get_optional_current_user(request: Request) -> User | None:
    """Trả về user đang đăng nhập hợp lệ, hoặc None (không báo lỗi)."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            return None

        # Kiểm tra phiên hợp lệ (thu hồi cookie cũ sau khi logout hoặc đổi mật khẩu)
        session_version = request.session.get("session_version")
        user_version = getattr(user, "session_version", None)
        if user_version is not None and session_version is not None:
            if session_version != user_version:
                return None

        # Tài khoản nhân viên: hồ sơ nhân viên phải còn hoạt động
        if user.role == ROLE_EMPLOYEE and user.employee_id:
            employee = db.get(Employee, user.employee_id)
            if employee is None or employee.status != EMPLOYEE_ACTIVE:
                return None

        return user


def get_current_user(request: Request) -> User:
    """Bắt buộc đăng nhập; nếu không hợp lệ thì xoá session và chuyển về trang login."""
    user = get_optional_current_user(request)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": LOGIN_URL})
    return user


def _require_role(role: str, message: str):
    """Tạo dependency chỉ cho phép đúng vai trò `role`."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail=message)
        return user

    return dependency


require_admin = _require_role(ROLE_ADMIN, "Bạn không có quyền truy cập trang quản trị")
require_employee = _require_role(ROLE_EMPLOYEE, "Chức năng chỉ dành cho nhân viên")
