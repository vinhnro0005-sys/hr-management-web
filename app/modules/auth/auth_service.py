from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.modules.auth.auth_models import User
from app.modules.auth.auth_repository import (
    add_user as repo_add_user,
    get_user_by_employee_id as repo_get_user_by_employee_id,
    get_user_by_id as repo_get_user_by_id,
    get_user_by_username as repo_get_user_by_username,
    update_user_password as repo_update_user_password,
)
from app.modules.auth.security import hash_password, verify_password

ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"
VALID_ROLES = (ROLE_ADMIN, ROLE_EMPLOYEE)
EMPLOYEE_ACTIVE = "Active"

# Kết quả trả về: (user, None) nếu thành công, (None, "lỗi") nếu thất bại
Result = tuple[User | None, str | None]


# ----------------------------------------------------------------------
# Repository delegation helpers
# ----------------------------------------------------------------------
def get_user_by_id(db: Session, user_id: int) -> User | None:
    return repo_get_user_by_id(db, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    return repo_get_user_by_username(db, username)


def check_employee_active(db: Session, employee_id: str | None) -> str | None:
    """Trả về thông báo lỗi nếu hồ sơ nhân viên có vấn đề, ngược lại trả None."""
    if not employee_id:
        return "Tài khoản nhân viên chưa liên kết với hồ sơ nhân viên"

    employee = db.get(Employee, employee_id)
    if employee is None or employee.status != EMPLOYEE_ACTIVE:
        return "Nhân viên liên kết đã ngừng hoạt động hoặc không tồn tại"

    return None


# ----------------------------------------------------------------------
# Xác thực & Đăng nhập
# ----------------------------------------------------------------------
def authenticate_user(db: Session, username: str, password: str) -> Result:
    username = (username or "").strip()
    password = password or ""

    if not username or not password:
        return None, "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu"

    user = repo_get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None, "Tên đăng nhập hoặc mật khẩu không chính xác"

    if not user.is_active:
        return None, "Tài khoản đã bị khóa"

    if user.role == ROLE_EMPLOYEE:
        error = check_employee_active(db, user.employee_id)
        if error:
            return None, error

    return user, None


# ----------------------------------------------------------------------
# Tạo người dùng
# ----------------------------------------------------------------------
def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = ROLE_EMPLOYEE,
    employee_id: str | None = None,
) -> Result:
    username = (username or "").strip()
    password = password or ""
    employee_id = employee_id or None  # chuỗi rỗng -> None

    # 1. Kiểm tra dữ liệu đầu vào
    if not username or not password:
        return None, "Tên đăng nhập và mật khẩu không được để trống"
    if len(username) > 100:
        return None, "Tên đăng nhập tối đa 100 ký tự"
    if len(password.encode("utf-8")) > 72:
        return None, "Mật khẩu tối đa 72 byte"
    if role not in VALID_ROLES:
        return None, "Vai trò không hợp lệ, chỉ chấp nhận admin hoặc employee"
    if repo_get_user_by_username(db, username) is not None:
        return None, "Tên đăng nhập đã tồn tại"

    # 2. Kiểm tra liên kết với nhân viên
    #    - employee: bắt buộc có employee_id
    #    - admin: không bắt buộc, nhưng nếu có thì phải đúng
    if role == ROLE_EMPLOYEE and not employee_id:
        return None, "Tài khoản nhân viên bắt buộc phải có mã nhân viên"

    if employee_id:
        if db.get(Employee, employee_id) is None:
            return None, "Không tìm thấy nhân viên tương ứng"

        if role == ROLE_EMPLOYEE:
            already_linked = repo_get_user_by_employee_id(db, employee_id)
            if already_linked is not None:
                return None, "Nhân viên này đã có tài khoản"

    # 3. Tạo user qua repository
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        employee_id=employee_id,
        is_active=True,
    )
    repo_add_user(db, user)
    db.commit()
    db.refresh(user)
    return user, None


# ----------------------------------------------------------------------
# Đổi mật khẩu
# ----------------------------------------------------------------------
def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> str | None:
    """Đổi mật khẩu cho user.

    Trả về None nếu thành công, trả về chuỗi lỗi nếu thất bại.
    """
    # 1. Xác thực mật khẩu hiện tại
    if not verify_password(current_password, user.password_hash):
        return "Mật khẩu hiện tại không chính xác"

    # 2. Kiểm tra mật khẩu mới
    new_password = new_password or ""
    if len(new_password) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự"
    if len(new_password.encode("utf-8")) > 72:
        return "Mật khẩu mới không được vượt quá 72 byte"

    # 3. Kiểm tra xác nhận mật khẩu
    if new_password != confirm_password:
        return "Xác nhận mật khẩu không khớp"

    # 4. Không cho phép đặt lại mật khẩu giống cũ
    if verify_password(new_password, user.password_hash):
        return "Mật khẩu mới không được trùng với mật khẩu hiện tại"

    # 5. Cập nhật hash mới vào DB và tăng session_version để thu hồi mọi phiên cũ
    repo_update_user_password(user, hash_password(new_password))
    user.session_version = (getattr(user, "session_version", 1) or 1) + 1
    db.commit()
    return None


# ----------------------------------------------------------------------
# Lớp AuthService giữ tương thích ngược 100% với code hiện có
# ----------------------------------------------------------------------
class AuthService:
    authenticate_user = staticmethod(authenticate_user)
    _check_employee_active = staticmethod(check_employee_active)
    get_user_by_id = staticmethod(get_user_by_id)
    get_user_by_username = staticmethod(get_user_by_username)
    create_user = staticmethod(create_user)
    change_password = staticmethod(change_password)
