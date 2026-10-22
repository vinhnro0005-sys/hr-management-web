from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from app.database import SessionLocal
#import nhan vien
from app.modules.employee import employee_service
from app.modules.employee.employee_schemas import (
    EmployeeCreate,
    EmployeeUpdate,
)
from app.modules.employee.employee_repository import get_employee_by_id


#import phong ban
from app.modules.department.department_repository import (
    get_all_departments,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def prepare_form_data(data: BaseModel):
    form_data = data.model_dump(mode="json")
    for field_name, value in form_data.items():
        if value is None:
            form_data[field_name] = ""

    return form_data


##-------EMPLOYEES----------
@router.get("/employees")
def list_employees(request: Request,
                   q: str = "",
                   department_id: str = "",
                   status: str = "",
                   position: str = "",
                ):
    with SessionLocal() as db:
        context = employee_service.get_employee_list_data(
            db=db,
            q=q,
            department_id=department_id,
            status=status,
            position=position,
        )

        return templates.TemplateResponse(
            request=request,
            name="employees/list.html",
            context=context
        )


#------tung nhan vien 1
@router.get("/employees/create")
def create_employee_form(request: Request):
    with SessionLocal() as db:
        departments = get_all_departments(db)
        return templates.TemplateResponse(
            request=request,
            name="employees/form.html",
            context={
                "departments": departments,
                "form_data": {},
            }
        )

@router.post("/employees/create")
def create_employee(
    request: Request,
    data: EmployeeCreate = Form(...),
):

    with SessionLocal() as db:
        error = employee_service.create_employee(db, data)

        if error is not None:
            form_data = prepare_form_data(data)

            departments = get_all_departments(db)
            return templates.TemplateResponse(
                request=request,
                name="employees/form.html",
                context={
                    "departments": departments,
                    "error": error,
                    "form_data": form_data,
                },
                status_code=400
            )

    return RedirectResponse(
        url = "/employees",
        status_code = 303
    )


@router.get("/employees/{employee_id}")
def employee_detail(request: Request, employee_id: str):
    with SessionLocal() as db:
        context = employee_service.get_employee_detail_data(
            db,
            employee_id,
        )
        return templates.TemplateResponse(
            request=request,
            name="employees/detail.html",
            context=context,
        )

@router.get("/employees/{employee_id}/edit")
def edit_employee_form(request: Request, employee_id: str):
    with SessionLocal() as db:
        context = employee_service.get_employee_edit_data(
            db,
            employee_id,
        )

        return templates.TemplateResponse(
            request=request,
            name="employees/edit.html",
            context=context,
        )

@router.post("/employees/{employee_id}/edit")
def update_employee(
        request: Request,
        employee_id: str,
        data: EmployeeUpdate = Form(...),
):

    with SessionLocal() as db:
        employee = get_employee_by_id(db, employee_id)
        if employee is None:
            raise HTTPException(
                status_code = 404,
                detail="Khong tim thay nhan vien"
            )
        error = employee_service.update_employee(db, employee, data)


        if error is not None:
            form_data = prepare_form_data(data)
            departments = get_all_departments(db)

            return templates.TemplateResponse(
                request=request,
                name="employees/edit.html",
                context={
                    "employee": employee,
                    "departments": departments,
                    "error": error,
                    "form_data": form_data
                },
                status_code = 400
            )
    return RedirectResponse(
        url = f"/employees/{employee_id}",
        status_code = 303
    )

@router.post("/employees/{employee_id}/deactivate")
def deactivate_employee(employee_id: str):
    with SessionLocal() as db:
        employee_service.deactive_employee(db, employee_id)
    return RedirectResponse(
        url = f"/employees/{employee_id}",
        status_code = 303
    )
