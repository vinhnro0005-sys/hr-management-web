from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.user import User
from app.modules.auth.security import hash_password, verify_password

ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"
VALID_ROLES = (ROLE_ADMIN, ROLE_EMPLOYEE)
EMPLOYEE_ACTIVE = "Active"

# Kết quả trả về: (user, None) nếu thành công, (None, "lỗi") nếu thất bại
Result = tuple[User | None, str | None]


class AuthService:
    # ------------------------------------------------------------------
    # Đăng nhập
    # ------------------------------------------------------------------
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Result:
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            return None, "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu"

        user = AuthService.get_user_by_username(db, username)
        if user is None or not verify_password(password, user.password_hash):
            return None, "Tên đăng nhập hoặc mật khẩu không chính xác"

        if not user.is_active:
            return None, "Tài khoản đã bị khóa"

        if user.role == ROLE_EMPLOYEE:
            error = AuthService._check_employee_active(db, user.employee_id)
            if error:
                return None, error

        return user, None

    @staticmethod
    def _check_employee_active(db: Session, employee_id: str | None) -> str | None:
        """Trả về thông báo lỗi nếu hồ sơ nhân viên có vấn đề, ngược lại trả None."""
        if not employee_id:
            return "Tài khoản nhân viên chưa liên kết với hồ sơ nhân viên"

        employee = db.get(Employee, employee_id)
        if employee is None or employee.status != EMPLOYEE_ACTIVE:
            return "Nhân viên liên kết đã ngừng hoạt động hoặc không tồn tại"

        return None

    # ------------------------------------------------------------------
    # Tìm user
    # ------------------------------------------------------------------
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id) if user_id else None

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        username = (username or "").strip()
        if not username:
            return None
        return db.scalar(select(User).where(User.username == username))

    # ------------------------------------------------------------------
    # Tạo user
    # ------------------------------------------------------------------
    @staticmethod
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
        if role not in VALID_ROLES:
            return None, "Vai trò không hợp lệ, chỉ chấp nhận admin hoặc employee"
        if AuthService.get_user_by_username(db, username):
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
                already_linked = db.scalar(
                    select(User).where(User.employee_id == employee_id)
                )
                if already_linked is not None:
                    return None, "Nhân viên này đã có tài khoản"

        # 3. Tạo user
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            employee_id=employee_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None