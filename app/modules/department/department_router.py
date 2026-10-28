from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.modules.department import department_service
from app.modules.department.department_repository import (
    get_all_departments,
    get_department_by_id,
)
from app.modules.department.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/departments")
def get_departments(request: Request):
    with SessionLocal() as db:
        departments = get_all_departments(db)
        return templates.TemplateResponse(
            request=request,
            name="departments/list.html",
            context={"departments": departments},
        )


@router.post("/departments/create")
def create_department(request: Request, data: DepartmentCreate = Form(...)):
    with SessionLocal() as db:
        error = department_service.create_department(db, data)
        if error:
            departments = get_all_departments(db)
            return templates.TemplateResponse(
                request=request,
                name="departments/list.html",
                context={
                    "departments": departments,
                    "error": error,
                    "entered_name": data.name,
                },
                status_code=400,
            )

    return RedirectResponse(
        url="/departments",
        status_code=303,
    )


@router.get("/departments/{department_id}/edit")
def edit_department_form(request: Request, department_id: int):
    with SessionLocal() as db:
        department = get_department_by_id(db, department_id)
        if department is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng ban",
            )
        return templates.TemplateResponse(
            request=request,
            name="departments/edit.html",
            context={"department": department},
        )


@router.post("/departments/{department_id}/edit")
def update_department(request: Request, department_id: int, data: DepartmentUpdate = Form(...)):
    with SessionLocal() as db:
        department = get_department_by_id(db, department_id)
        if department is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng ban"
            )
        error = department_service.update_department(db, department, data)
        if error:
            return templates.TemplateResponse(
                request=request,
                name="departments/edit.html",
                context={
                    "department": department,
                    "error": error,
                    "entered_name": data.name
                },
                status_code=400,
            )
    return RedirectResponse(
        url="/departments",
        status_code=303
    )
