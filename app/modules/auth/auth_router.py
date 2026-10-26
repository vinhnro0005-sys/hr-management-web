from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.modules.auth.auth_service import AuthService
from app.modules.auth.dependencies import get_current_user, get_optional_current_user
from app.modules.auth.security import generate_csrf_token, verify_csrf_token

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

# ---------------------------------------------------------------------------
# Hằng số: sửa ở một chỗ, dùng ở mọi nơi
# ---------------------------------------------------------------------------
ADMIN_ROLE = "admin"
LOGIN_URL = "/login"
ADMIN_HOME_URL = "/dashboard"
USER_HOME_URL = "/profile"


# ---------------------------------------------------------------------------
# Hàm hỗ trợ (helper)
# ---------------------------------------------------------------------------
def redirect(url: str) -> RedirectResponse:
    """Chuyển trang sau khi POST (303 = Post/Redirect/Get)."""
    return RedirectResponse(url=url, status_code=303)


def redirect_by_role(user: User) -> RedirectResponse:
    """Admin về trang nhân viên, người dùng thường về trang cá nhân."""
    if user.role == ADMIN_ROLE:
        return redirect(ADMIN_HOME_URL)
    return redirect(USER_HOME_URL)


def get_csrf_token(request: Request) -> str:
    """Lấy CSRF token trong session; chưa có thì tạo mới."""
    token = request.session.get("csrf_token")
    if not token:
        token = generate_csrf_token()
        request.session["csrf_token"] = token
    return token


def refresh_csrf_token(request: Request) -> str:
    """Luôn tạo CSRF token mới và lưu vào session."""
    token = generate_csrf_token()
    request.session["csrf_token"] = token
    return token


def render_login_error(request: Request, message: str, username: str = ""):
    """Hiện lại trang đăng nhập kèm thông báo lỗi."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": message,
            "username": username,
            "csrf_token": refresh_csrf_token(request),
        },
        status_code=400,
    )


# ---------------------------------------------------------------------------
# Đăng nhập
# ---------------------------------------------------------------------------
@router.get("/login")
def login_page(request: Request):
    # Đã đăng nhập rồi thì không cần xem form nữa
    user = get_optional_current_user(request)
    if user is not None:
        return redirect_by_role(user)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"csrf_token": get_csrf_token(request)},
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    csrf_token: str = Form(""),
):
    # Bước 1: kiểm tra CSRF
    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        return render_login_error(
            request,
            "Phiên làm việc không hợp lệ hoặc thiếu mã CSRF. Vui lòng thử lại.",
            username,
        )

    # Bước 2: kiểm tra đã nhập đủ thông tin chưa
    username = username.strip()
    if not username or not password:
        return render_login_error(
            request, "Vui lòng nhập tên đăng nhập và mật khẩu.", username
        )

    # Bước 3: xác thực với database
    with SessionLocal() as db:
        user, error = AuthService.authenticate_user(db, username, password)
        if error:
            return render_login_error(request, error, username)
        user_id = user.id
        redirect_response = redirect_by_role(user)

    # Bước 4: đăng nhập thành công -> xoá session cũ rồi tạo session mới
    # (chống session fixation)
    request.session.clear()
    request.session["user_id"] = user_id
    refresh_csrf_token(request)

    return redirect_response


# ---------------------------------------------------------------------------
# Đăng xuất
# ---------------------------------------------------------------------------
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect(LOGIN_URL)


@router.get("/logout")
def logout_get(request: Request):
    request.session.clear()
    return redirect(LOGIN_URL)


# ---------------------------------------------------------------------------
# Trang cá nhân
# ---------------------------------------------------------------------------
def load_employee_and_department(employee_id: int | None):
    """Lấy nhân viên và phòng ban; trả về (None, None) nếu không có."""
    if not employee_id:
        return None, None

    with SessionLocal() as db:
        employee = db.get(Employee, employee_id)
        if employee is None:
            return None, None
        department = db.get(Department, employee.department_id)
        return employee, department


@router.get("/profile")
def profile(request: Request, current_user: User = Depends(get_current_user)):
    employee, department = load_employee_and_department(current_user.employee_id)

    return templates.TemplateResponse(
        request=request,
        name="profile/profile.html",
        context={
            "user": current_user,
            "employee": employee,
            "department": department,
            "csrf_token": get_csrf_token(request),
        },
    )
