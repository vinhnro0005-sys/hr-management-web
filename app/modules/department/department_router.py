from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select

from app.database import SessionLocal
from app.models.department import Department

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

##---------DEPARTMENT-----------
@router.get("/departments")
def get_departments(request: Request):
    with SessionLocal() as db:
        departments = db.scalars(
            select(Department).order_by(Department.id)
        ).all()
        return templates.TemplateResponse(
            request=request,
            name="departments/list.html",
            context={"departments": departments},
        )

@router.post("/departments/create")
def create_department(request: Request, name: str = Form(...)):
    name = name.strip()
    error = None
    with SessionLocal() as db:
        if not name:
            error = "Tên phòng ban không được để trống"
        elif len(name) > 100:
            error = "Tên phòng ban tối đa 100 ký tự"
        else:
            existing_department = db.scalar(
                select(Department).where(Department.name == name)
            )
            if existing_department is not None:
                error = "Tên phòng ban đã tồn tại"

        if error:
            department = db.scalars(
                select(Department).order_by(Department.id)
            ).all()
            return templates.TemplateResponse(
                request = request,
                name = "departments/list.html",
                context = {
                    "departments": department,
                    "error": error,
                },
                status_code = 400,
            )
        department = Department(name=name)
        db.add(department)
        db.commit()

    return RedirectResponse(
        url = "/departments",
        status_code = 303,
    )

@router.get("/departments/{department_id}/edit")
def edit_department_form(request: Request, department_id: int):
    with SessionLocal() as db:
        department = db.get(Department, department_id)
        if department is None:
            raise HTTPException(
                status_code = 404,
                detail = "Không tìm thấy phòng ban",
            )
        return templates.TemplateResponse(
            request = request,
            name = "departments/edit.html",
            context = {"department": department},
        )

@router.post("/departments/{department_id}/edit")
def update_department(request: Request, department_id: int, name: str = Form(...)):
    name = name.strip()
    error = None
    with SessionLocal() as db:
        department = db.get(Department, department_id)
        if department is None:
            raise HTTPException(
                status_code = 404,
                detail = "Không tìm thấy tài khoản"
            )
        if not name:
            error = "Tên phòng ban không được để trống"
        elif len(name) > 100:
            error = "Tên phòng ban tối đa 100 ksy tự"
        else:
            existing_department = db.scalar(
                select(Department).where(
                    Department.name == name,
                    Department.id != department_id
                )
            )
            if existing_department is not None:
                error = "Tên phòng ban đã tồn tại"
        if error:
            return templates.TemplateResponse(
                request = request,
                name = "departments/edit.html",
                context = {"department": department, "error": error},
                status_code = 400,
            )
        department.name = name
        db.commit()
    return RedirectResponse(
        url="/departments",
        status_code = 303
    )
