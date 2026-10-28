from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError

from app.database import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.modules.auth.auth_service import AuthService
from app.modules.auth.dependencies import get_current_user, get_optional_current_user
from app.modules.auth.security import generate_csrf_token, verify_csrf_token
from app.modules.department.department_repository import get_all_departments
from app.modules.employee import employee_service
from app.modules.employee.employee_repository import get_employee_by_id
from app.modules.employee.employee_schemas import EmployeeUpdate

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
def logout(request: Request, csrf_token: str = Form("")):
    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Phiên làm việc đã hết hạn hoặc thiếu mã CSRF. Hãy tải lại trang rồi thử lại.",
        )
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


def prepare_form_data(data: BaseModel):
    form_data = data.model_dump(mode="json")
    for field_name, value in form_data.items():
        if value is None:
            form_data[field_name] = ""
    return form_data


# ---------------------------------------------------------------------------
# Chỉnh sửa thông tin cá nhân
# ---------------------------------------------------------------------------
@router.get("/profile/edit")
def edit_profile_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.employee_id:
        return redirect("/profile")

    with SessionLocal() as db:
        context = employee_service.get_employee_edit_data(db, current_user.employee_id)
        context["user"] = current_user
        context["csrf_token"] = get_csrf_token(request)
        context["profile_mode"] = True
        return templates.TemplateResponse(
            request=request,
            name="profile/edit.html",
            context=context,
        )


class ProfileUpdateForm(BaseModel):
    """Form tự sửa hồ sơ: gộp csrf_token vào cùng model để tránh lỗi 422.

    FastAPI không cho trộn một model Form với tham số Form rời.
    Phòng ban, chức vụ, ngày vào làm do quản trị viên quản lý nên không có ở đây.
    """

    csrf_token: str = ""
    name: str = ""
    gender: str | None = None
    birthday: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


@router.post("/profile/edit")
def update_profile(
    request: Request,
    form: ProfileUpdateForm = Form(...),
    current_user: User = Depends(get_current_user),
):
    csrf_token = form.csrf_token
    if not current_user.employee_id:
        return redirect("/profile")

    # Kiểm tra CSRF
    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        with SessionLocal() as db:
            context = employee_service.get_employee_edit_data(db, current_user.employee_id)
            context["user"] = current_user
            context["csrf_token"] = refresh_csrf_token(request)
            context["error"] = "Phiên làm việc không hợp lệ hoặc thiếu mã CSRF. Vui lòng thử lại."
            context["profile_mode"] = True
            return templates.TemplateResponse(
                request=request,
                name="profile/edit.html",
                context=context,
                status_code=400,
            )

    with SessionLocal() as db:
        employee = get_employee_by_id(db, current_user.employee_id)
        if employee is None:
            return redirect("/profile")

        # Phòng ban, chức vụ, ngày vào làm luôn giữ giá trị hiện có.
        submitted = form.model_dump(exclude={"csrf_token"})
        try:
            data = EmployeeUpdate(
                **submitted,
                department_id=employee.department_id,
                position=employee.position,
                start_date=employee.start_date,
            )
            error = employee_service.update_employee(db, employee, data)
        except ValidationError as exc:
            first = exc.errors()[0]
            error = {
                "field": str(first["loc"][0]) if first["loc"] else "",
                "message": first["msg"].removeprefix("Value error, "),
            }

        if error is not None:
            form_data = {k: (v or "") for k, v in submitted.items()}
            form_data["department_id"] = employee.department_id
            form_data["position"] = employee.position or ""
            form_data["start_date"] = (
                employee.start_date.isoformat() if employee.start_date else ""
            )
            departments = get_all_departments(db)
            return templates.TemplateResponse(
                request=request,
                name="profile/edit.html",
                context={
                    "user": current_user,
                    "employee": employee,
                    "departments": departments,
                    "error": error["message"],
                    "field_errors": {error["field"]: error["message"]},
                    "form_data": form_data,
                    "csrf_token": get_csrf_token(request),
                    "profile_mode": True,
                },
                status_code=400,
            )

    return redirect("/profile")


# ---------------------------------------------------------------------------
# Đổi mật khẩu
# ---------------------------------------------------------------------------
@router.get("/profile/change-password")
def change_password_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if current_user.role == ADMIN_ROLE:
        return redirect("/profile")

    return templates.TemplateResponse(
        request=request,
        name="profile/change_password.html",
        context={
            "user": current_user,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/profile/change-password")
def change_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    csrf_token: str = Form(""),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == ADMIN_ROLE:
        return redirect("/profile")
    # Kiểm tra CSRF
    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        return templates.TemplateResponse(
            request=request,
            name="profile/change_password.html",
            context={
                "user": current_user,
                "csrf_token": refresh_csrf_token(request),
                "error": "Phiên làm việc không hợp lệ hoặc thiếu mã CSRF. Vui lòng thử lại.",
            },
            status_code=400,
        )

    with SessionLocal() as db:
        user = db.get(User, current_user.id)
        if user is None:
            return redirect(LOGIN_URL)
        error = AuthService.change_password(
            db=db,
            user=user,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

    if error:
        return templates.TemplateResponse(
            request=request,
            name="profile/change_password.html",
            context={
                "user": current_user,
                "csrf_token": get_csrf_token(request),
                "error": error,
            },
            status_code=400,
        )

    # Thành công → đăng xuất để bắt đăng nhập lại với mật khẩu mới
    request.session.clear()
    return redirect(LOGIN_URL + "?changed=1")
