import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.modules.auth.auth_router import router as auth_router
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import SessionLocal

from app.modules.department.department_repository import (
    get_all_departments,
    get_department_by_id,
)
from app.modules.department.department_router import router as department_router


from app.modules.employee.employee_repository import get_employee_by_id
from app.modules.employee.employee_router import router as employee_router
from app.modules.employee.csrf import require_csrf

from app.modules.dashboard.dashboard_router import router as dashboard_router

app = FastAPI(title="HR Management System")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="session",
    max_age=14 * 24 * 3600,
    same_site="lax",
    https_only=False,
)

# Đăng ký các router
app.include_router(auth_router)
app.include_router(department_router, dependencies=[Depends(require_admin), Depends(require_csrf)])
app.include_router(employee_router, dependencies=[Depends(require_admin), Depends(require_csrf)])
app.include_router(dashboard_router)

templates = Jinja2Templates(directory="app/templates")

@app.exception_handler(StarletteHTTPException)
async def http_not_found(request: Request, exc: StarletteHTTPException):
    wants_html = "text/html" in request.headers.get("accept", "")
    if exc.status_code == 404 and wants_html:
        message = exc.detail if exc.detail != "Not Found" else None
        return templates.TemplateResponse(
            request=request,
            name="errors/404.html",
            context={"message": message, "user": get_optional_current_user(request)},
            status_code=404,
        )
    if exc.status_code == 403 and wants_html:
        return templates.TemplateResponse(
            request=request,
            name="errors/403.html",
            context={"message": exc.detail, "user": get_optional_current_user(request)},
            status_code=403,
        )
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    route = request.scope.get("route")
    route_name = getattr(route, "name", None)

    if request.method == "POST" and route_name in ("create_employee", "update_employee", "update_profile"):
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

        first_error = exc.errors()[0]
        field_name = first_error["loc"][-1]
        label = field_names.get(field_name, "Dữ liệu")
        error_type = first_error["type"]
        details = first_error.get("ctx", {})

        error = f"{label} không hợp lệ"

        if error_type == "missing":
            error = f"{label} không được để trống"

        elif error_type == "string_too_short":
            error = f"{label} không được để trống"
        elif error_type == "string_too_long":
            max_length = details["max_length"]
            error = f"{label} tối đa {max_length} ký tự"
        elif error_type == "value_error":
            error = str(details["error"])

        form = await request.form()
        form_data = dict(form)

        with SessionLocal() as db:
            departments = get_all_departments(db)
            context = {
                "departments": departments,
                "error": error,
                "form_data": form_data,
                "field_errors": {str(field_name): error},
            }
            if route_name == "create_employee":
                template_name = "employees/form.html"
            elif route_name == "update_profile":
                user = get_optional_current_user(request)
                if user and user.employee_id:
                    employee = get_employee_by_id(db, user.employee_id)
                    context["employee"] = employee
                    context["user"] = user
                template_name = "profile/edit.html"
            else:
                employee_id = request.path_params["employee_id"]
                employee = get_employee_by_id(db, employee_id)

                if employee is None:
                    return HTMLResponse(
                        content="Không tìm thấy nhân viên",
                        status_code = 404,
                    )
                template_name = "employees/edit.html"
                context["employee"] = employee
            return templates.TemplateResponse(
                request=request,
                name=template_name,
                context=context,
                status_code = 400
            )

    is_department_form = (
        request.method == "POST"
        and route_name in ("create_department", "update_department")
    )

    if not is_department_form:
        return await request_validation_exception_handler(request, exc)

    for validation_error in exc.errors():
        if validation_error["loc"][0] == "path":
            return await request_validation_exception_handler(request, exc)

    messages = {
        "missing": "Tên phòng ban không được để trống",
        "string_too_short": "Tên phòng ban không được để trống",
        "string_too_long": "Tên phòng ban tối đa 100 ký tự"
    }

    first_error = exc.errors()[0]
    error = messages.get(
        first_error["type"],
        "Tên phòng ban không hợp lệ"
    )
    form = await request.form()
    entered_name = form.get("name", "")
    context = {
        "error": error,
        "entered_name": entered_name,
    }
    with SessionLocal() as db:
        if route_name == "create_department":
            template_name = "departments/list.html"
            context["departments"] = get_all_departments(db)

        else:
            department_id = int(request.path_params["department_id"])
            department = get_department_by_id(db, department_id)
            if department is None:
                return HTMLResponse(
                    content="Không tìm thấy phòng ban",
                    status_code = 404,
                )
            template_name = "departments/edit.html"
            context["department"] = department
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            status_code=400,
        )

@app.get("/")
def home(request: Request):
    user = get_optional_current_user(request)
    if user is not None:
        if user.role == "admin":
            return RedirectResponse(url="/dashboard", status_code=303)
        return RedirectResponse(url="/profile", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/about")
def about():
    return {
        "project": "HR Management",
        "backend": "FastAPI",
    }


# ----CHAY BANG UVICORN----
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


#FE BO SUNG
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="app/static"), name="static")

