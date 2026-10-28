from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.user import User
from app.modules.auth.dependencies import require_admin
from app.modules.dashboard import dashboard_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(
        request: Request,
        current_user: User = Depends(require_admin),

):
    with SessionLocal() as db:
        context = dashboard_service.get_dashboard_data(db)
        context["user"] = current_user

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context=context,
        )
