import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.modules.auth.auth_router import router as auth_router
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.department.department_router import router as department_router
from app.modules.employee.employee_router import router as employee_router

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
app.include_router(department_router, dependencies=[Depends(require_admin)])
app.include_router(employee_router, dependencies=[Depends(require_admin)])


@app.get("/")
def home(request: Request):
    user = get_optional_current_user(request)
    if user is not None:
        if user.role == "admin":
            return RedirectResponse(url="/employees", status_code=303)
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