from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError

from app.core.email import send_email
from app.core.database import SessionLocal
from app.modules.department.department_models import Department
from app.modules.employee.employee_models import Employee
from app.modules.auth.auth_models import User
from app.modules.auth.auth_repository import get_user_by_id
from app.modules.auth.auth_service import AuthService
from app.modules.auth.dependencies import get_current_user, get_optional_current_user
from app.modules.auth.security import (
    generate_csrf_token,
    generate_password_reset_token,
    verify_csrf_token,
    verify_password_reset_token,
)
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
    request.session["session_version"] = getattr(user, "session_version", 1)
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
    user_id = request.session.get("user_id")
    if user_id:
        with SessionLocal() as db:
            user = get_user_by_id(db, user_id)
            if user is not None:
                user.session_version = (getattr(user, "session_version", 1) or 1) + 1
                db.commit()
    request.session.clear()
    return redirect(LOGIN_URL)


# ---------------------------------------------------------------------------
# Trang cá nhân
# ---------------------------------------------------------------------------
def load_employee_and_department(employee_id: str | None):
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


def format_validation_error(exc: ValidationError) -> dict:
    """Chuyển lỗi Pydantic thành thông báo tiếng Việt thân thiện."""
    field_names = {
        "id": "Mã nhân viên",
        "name": "Họ tên",
        "department_id": "Phòng ban",
        "position": "Chức vụ",
        "phone": "Điện thoại",
        "email": "Email",
        "address": "Địa chỉ",
        "gender": "Giới tính",
        "birthday": "Ngày sinh",
        "start_date": "Ngày vào làm",
    }
    first = exc.errors()[0]
    field = str(first["loc"][0]) if first["loc"] else ""
    label = field_names.get(field, "Dữ liệu")
    error_type = first.get("type", "")
    ctx = first.get("ctx", {})
    msg = first.get("msg", "")

    if error_type in ("missing", "string_too_short") or "at least 1 character" in msg:
        message = f"{label} không được để trống"
    elif error_type == "string_too_long" or "at most" in msg:
        max_length = ctx.get("max_length", 100)
        message = f"{label} tối đa {max_length} ký tự"
    elif "value_error" in error_type:
        message = msg.removeprefix("Value error, ")
    elif error_type in ("enum", "literal_error") or "Input should be" in msg:
        message = f"{label} phải là 'Nam', 'Nữ' hoặc 'Khác'"
    else:
        message = f"{label} không hợp lệ"

    return {"field": field, "message": message}


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
            error = format_validation_error(exc)

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
        user = get_user_by_id(db, current_user.id)
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


# ---------------------------------------------------------------------------
# Quên mật khẩu & Đặt lại mật khẩu (Dành cho nhân viên)
# ---------------------------------------------------------------------------

# 1. Trang nhập email để lấy link reset
@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    """Trang nhập email để gửi yêu cầu đặt lại mật khẩu."""
    user = get_optional_current_user(request)
    if user is not None:
        return redirect_by_role(user)

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "csrf_token": get_csrf_token(request),
            "page_title": "Quên mật khẩu",
        },
    )


# 2. Xử lý gửi email chứa token
@router.post("/forgot-password")
def handle_forgot_password(
    request: Request,
    email: str = Form(""),
    csrf_token: str = Form(""),
):
    """Xử lý tra cứu nhân viên và gửi email chứa liên kết token bảo mật."""
    clean_email = (email or "").strip().lower()

    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "error": "Phiên làm việc đã hết hạn hoặc mã CSRF không hợp lệ.",
                "email": clean_email,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Quên mật khẩu",
            },
            status_code=400,
        )

    if not clean_email:
        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "error": "Vui lòng nhập địa chỉ email của nhân viên.",
                "email": clean_email,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Quên mật khẩu",
            },
            status_code=400,
        )

    with SessionLocal() as db:
        user, employee = AuthService.get_user_by_employee_email(db, clean_email)
        is_emp_active = bool(employee and employee.status and employee.status.strip().lower() in ("active", "đang làm việc", "hoạt động"))
        if user and employee and user.is_active and is_emp_active:
            token = generate_password_reset_token(user.id, getattr(user, "session_version", 1) or 1)
            base_url = str(request.base_url).rstrip("/")
            reset_link = f"{base_url}/reset-password?token={token}"

            sent = send_email(
                to_email=employee.email,
                subject="[HR Management] Hướng dẫn đặt lại mật khẩu nhân viên",
                template_name="emails/reset_password.html",
                context={
                    "name": employee.name,
                    "reset_link": reset_link,
                    "expires_minutes": 15,
                },
            )

            print("\n" + "=" * 65)
            print(f"[RESET PASSWORD] Tìm thấy nhân viên: {employee.name} (Mã: {employee.id}, Email: {employee.email})")
            print(f"[RESET PASSWORD LINK] {reset_link}")
            if sent:
                print(f"[RESET PASSWORD] -> Đã gửi email đặt lại mật khẩu thành công qua SMTP.")
            else:
                print(f"[RESET PASSWORD WARNING] -> Không gửi được qua SMTP. Bạn có thể mở trực tiếp link trên để đổi mật khẩu.")
            print("=" * 65 + "\n")
        else:
            print(f"\n[RESET PASSWORD] Không tìm thấy tài khoản nhân viên hợp lệ với email: '{clean_email}'")
            print("[RESET PASSWORD HINT] Lưu ý: Chỉ nhân viên có email trong CSDL (bảng employees) mới nhận được link. Tài khoản admin thuần túy không có email trong CSDL.\n")

    # Luôn báo thành công chung để bảo vệ quyền riêng tư người dùng
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "success": "Nếu email tồn tại trên hệ thống, liên kết đặt lại mật khẩu đã được gửi đến hòm thư của bạn. Vui lòng kiểm tra email (bao gồm cả thư mục Spam).",
            "csrf_token": refresh_csrf_token(request),
            "page_title": "Quên mật khẩu",
        },
    )


# 3. Trang đặt mật khẩu mới khi người dùng click link từ email
@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    """Trang biểu mẫu đặt lại mật khẩu mới từ liên kết trong email."""
    token = (token or "").strip()
    if not token:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Liên kết không hợp lệ hoặc thiếu mã xác thực.",
                "token": "",
                "csrf_token": get_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    data = verify_password_reset_token(token, max_age=900)
    if not data:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Liên kết đặt lại mật khẩu đã hết hạn (sau 15 phút) hoặc không hợp lệ. Vui lòng yêu cầu lại.",
                "token": "",
                "csrf_token": get_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    user_id = data.get("user_id")
    token_v = data.get("v")
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        if not user or not user.is_active or (getattr(user, "session_version", 1) or 1) != token_v:
            return templates.TemplateResponse(
                request=request,
                name="reset_password.html",
                context={
                    "error": "Liên kết này đã được sử dụng hoặc tài khoản không khả dụng. Vui lòng gửi lại yêu cầu mới.",
                    "token": "",
                    "csrf_token": get_csrf_token(request),
                    "page_title": "Đặt lại mật khẩu",
                },
                status_code=400,
            )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "token": token,
            "csrf_token": get_csrf_token(request),
            "page_title": "Đặt lại mật khẩu",
        },
    )


# 4. Xử lý lưu mật khẩu mới
@router.post("/reset-password")
def handle_reset_password(
    request: Request,
    token: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(None),
    csrf_token: str = Form(""),
):
    """Xử lý cập nhật mật khẩu mới và hủy bỏ token/phiên đăng nhập cũ."""
    token = (token or "").strip()
    new_password = new_password or ""

    if not verify_csrf_token(request.session.get("csrf_token"), csrf_token):
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Phiên làm việc đã hết hạn hoặc mã CSRF không hợp lệ.",
                "token": token,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    data = verify_password_reset_token(token, max_age=900)
    if not data:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Liên kết đặt lại mật khẩu đã hết hạn (sau 15 phút) hoặc không hợp lệ. Vui lòng yêu cầu lại.",
                "token": "",
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    if len(new_password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Mật khẩu mới phải có ít nhất 8 ký tự.",
                "token": token,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    if len(new_password.encode("utf-8")) > 72:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Mật khẩu không được vượt quá 72 byte.",
                "token": token,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    if confirm_password is not None and new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Xác nhận mật khẩu mới không khớp.",
                "token": token,
                "csrf_token": refresh_csrf_token(request),
                "page_title": "Đặt lại mật khẩu",
            },
            status_code=400,
        )

    user_id = data.get("user_id")
    token_v = data.get("v")
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        if not user or not user.is_active or (getattr(user, "session_version", 1) or 1) != token_v:
            return templates.TemplateResponse(
                request=request,
                name="reset_password.html",
                context={
                    "error": "Liên kết này đã được sử dụng hoặc tài khoản không khả dụng.",
                    "token": "",
                    "csrf_token": refresh_csrf_token(request),
                    "page_title": "Đặt lại mật khẩu",
                },
                status_code=400,
            )

        error = AuthService.reset_password_with_token(db, user, new_password)
        if error:
            return templates.TemplateResponse(
                request=request,
                name="reset_password.html",
                context={
                    "error": error,
                    "token": token,
                    "csrf_token": refresh_csrf_token(request),
                    "page_title": "Đặt lại mật khẩu",
                },
                status_code=400,
            )

    request.session.clear()
    return redirect(LOGIN_URL + "?reset=1")
