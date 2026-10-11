import re
from datetime import date
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, or_

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.department import Department

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

##------kiem tra email-----
def is_valid_email(email: str):
    pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    result = re.fullmatch(pattern, email)

    if result is None:
        return False
    return True


##-------EMPLOYEES----------
@router.get("/employees")
def list_employees(request: Request,
                   q: str = "",
                   department_id: str = "",
                   status: str = "",
                   position: str = "",
                ):
    q = q.strip()
    with SessionLocal() as db:
        #id phong ban vs status
        departments = db.scalars(
            select(Department).order_by(Department.id)
        ).all()

        position_statement = select(Employee.position)
        position_statement = position_statement.where(
            Employee.position.is_not(None)
        )
        position_statement = position_statement.where(
            Employee.position != ""
        )
        position_statement = position_statement.distinct()
        position_statement = position_statement.order_by(
            Employee.position
        )
        position_result = db.scalars(position_statement)
        positions = position_result.all()

        valid_department_ids = set()
        for department in departments:
            valid_department_ids.add(str(department.id))
        if department_id and department_id not in valid_department_ids:
            raise HTTPException(
                status_code=400,
                detail="Phong ban khong hop le"
            )
        if status not in ("", "Active", "Inactive"):
            raise HTTPException(
                status_code=400,
                detail="Trang thai khong hop le"
            )
        if position != "":
            if position not in positions:
                raise HTTPException(
                    status_code=400,
                    detail="Chuc vu khong hop le"
                )

        #xu ly q
        statement = (
            select(Employee, Department.name)
            .join(
                Department,
                Employee.department_id == Department.id
            )
        )
        if q:
            statement = statement.where(
                or_(
                    Employee.id.contains(q, autoescape=True),
                    Employee.name.contains(q, autoescape=True)
                )
            )
        if department_id:
            statement = statement.where(
                Employee.department_id == int(department_id)
            )
        if status:
            statement = statement.where(
                Employee.status == status
            )
        if position:
            statement = statement.where(
                Employee.position == position
            )
        employees = db.execute(
            statement.order_by(Employee.id)
        ).all()
        return templates.TemplateResponse(
            request=request,
            name="employees/list.html",
            context={"employees": employees,
                     "q": q,
                     "departments": departments,
                     "positions": positions,
                     "selected_department": department_id,
                     "selected_status": status,
                     "selected_position": position
                 }
        )


#------tung nhan vien 1
@router.get("/employees/create")
def create_employee_form(request: Request):
    with SessionLocal() as db:
        department = db.scalars(
            select(Department).order_by(Department.id)
        ).all()
        return templates.TemplateResponse(
            request=request,
            name="employees/form.html",
            context={
                "departments": department,
                "form_data": {},
            }
        )

@router.post("/employees/create")
def create_employee(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    department_id: int = Form(...),
    position: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    gender: str = Form(""),
    address: str = Form(""),
    birthday: date | None = Form(None),
    start_date: date | None =  Form(None)
):
    employee_id = id.strip()
    name = name.strip()
    position = position.strip()
    phone = phone.strip()
    email = email.strip()
    gender = gender.strip()
    address = address.strip()
    error = None

    #--luu form nhap thong tin neu nhap loi-----
    birthday_value = ""
    if birthday is not None:
        birthday_value = birthday.isoformat()
    start_date_value = ""
    if start_date is not None:
        start_date_value = start_date.isoformat()
    form_data = {
        "id": employee_id,
        "name": name,
        "department_id": department_id,
        "position": position,
        "email": email,
        "gender": gender,
        "phone": phone,
        "address": address,
        "birthday": birthday_value,
        "start_date": start_date_value,
    }

    with SessionLocal() as db:
        if not employee_id or not name:
            error = "Mã và tên nhân viên không được để trống"
        elif len(phone)>20:
            error = "Dien thoai toi da 20 ky tu"
        elif len(email)>255:
            error = "Email toi da 255 ky tu"
        elif email != "" and not is_valid_email(email):
            error = "Email ko dung dinh dang"
        elif len(employee_id)>20 or len(name)>100:
            error = "Mã tối đa 20 ký tự, tên tối đa 100 k tự"
        elif len(position) > 100:
            error = "Chức vụ tối đa 100 ký tự"
        elif gender not in ("", "Nam", "Nữ", "Khác"):
            error = "Gioi tinh khong hop le"
        elif len(address)>255:
            error = "Dia chi toi da 255 ky tu"
        elif birthday is not None and birthday>date.today():
            error = "Ngay sinh ko dc nam trong tuong lai"
        elif birthday is not None and start_date is not None and start_date<birthday:
            error = "Ngay vao lam ko dc trc ngay sinh"

        elif db.get(Employee, employee_id) is not None:
            error = "Mã nhân vien đã tồn tại"
        elif db.get(Department, department_id) is None:
            error = "Phòng ban ko tồn tại"

        if error is None and email:
            existing_employee = db.scalar(
                select(Employee).where(Employee.email==email)
            )
            if existing_employee is not None:
                error = "Email da dc su dung"
        if error:
            departments = db.scalars(
                select(Department).order_by(Department.id)
            ).all()
            return templates.TemplateResponse(
                request=request,
                name="employees/form.html",
                context={
                    "departments": departments,
                    "error": error,
                    "form_data": form_data,
                },
                status_code = 400
            )
        employee = Employee(
            id=employee_id,
            name=name,
            department_id = department_id,
            position = position or None,
            phone=phone or None,
            email=email or None,
            gender=gender or None,
            address=address or None,
            birthday=birthday,
            start_date=start_date,
            status = "Active"
        )
        db.add(employee)
        db.commit()
    return RedirectResponse(
        url = "/employees",
        status_code = 303
    )


@router.get("/employees/{employee_id}")
def employee_detail(request: Request, employee_id: str):
    with SessionLocal() as db:
        employee = db.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(
                status_code = 404,
                detail="Khong tim thay nhan vien"
            )
        department = db.get(
            Department,
            employee.department_id
        )
        return templates.TemplateResponse(
            request=request,
            name="employees/detail.html",
            context={"employee": employee, "department": department},
        )

@router.get("/employees/{employee_id}/edit")
def edit_employee_form(request: Request, employee_id: str):
    with SessionLocal() as db:
        employee = db.get(Employee, employee_id)

        if employee is None:
            raise HTTPException(
                status_code = 404,
                detail = "Khong tim thay nhan vien"
            )
        departments = db.scalars(
            select(Department).order_by(Department.id)
        ).all()

        ##them form_data vao----tuong tu trong ham create
        birthday_value = ""
        if employee.birthday is not None:
            birthday_value = employee.birthday.isoformat()
        start_date_value = ""
        if employee.start_date is not None:
            start_date_value = employee.start_date.isoformat()

        form_data = {
            "name": employee.name,
            "department_id": employee.department_id,
            "position": employee.position,
            "phone": employee.phone,
            "email": employee.email,
            "gender": employee.gender,
            "address": employee.address,
            "birthday": employee.birthday,
            "start_date": employee.start_date,

        }

        return templates.TemplateResponse(
            request=request,
            name="employees/edit.html",
            context={
                "employee": employee,
                "departments": departments,
                "form_data": form_data
            }
        )

@router.post("/employees/{employee_id}/edit")
def update_employee(
        request: Request,
        employee_id: str,
        name: str = Form(...),
        department_id: int = Form(...),
        position: str = Form(""),
        phone: str = Form(""),
        email: str = Form(""),
        gender: str = Form(""),
        address: str = Form(""),
        birthday: date | None = Form(None),
        start_date: date | None = Form(None)
):
    name = name.strip()
    position = position.strip()
    phone = phone.strip()
    email = email.strip()
    gender = gender.strip()
    address = address.strip()
    error = None

    #form_data tuong tu trong get
    birthday_value = ""
    if birthday is not None:
        birthday_value = birthday.isoformat()
    start_date_value = ""
    if start_date is not None:
        start_date_value = start_date.isoformat()

    form_data = {
        "name": name,
        "department_id": department_id,
        "position": position,
        "phone": phone,
        "email": email,
        "gender": gender,
        "address": address,
        "birthday": birthday_value,
        "start_date": start_date_value,
    }

    with SessionLocal() as db:
        employee = db.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(
                status_code = 404,
                detail="Khong tim thay nhan vien"
            )
        if not name:
            error = "Ho ten khong duoc de trong"
        elif len(name)>100:
            error = "Ho ten toi da 100 ky tu"
        elif len(position)>100:
            error = "Chuc vu toi da 100 ky tu"
        elif db.get(Department, department_id) is None:
            error = "Phong ban khong ton tai"
        elif len(phone)>20:
            error = "Dien thoai toi da 20 ky tu"
        elif len(email)>255:
            error = "email toi da 255 ky tu"
        elif email != "" and not is_valid_email(email):
            error = "Email chua dung dinh dang"
        elif birthday is not None and birthday>date.today():
            error = "NGAY sinh khong dc nam trong tuong lai"
        elif(
            birthday is not None
            and start_date is not None
            and start_date < birthday
        ):
            error = "ngay vao lam ko dc trc ngay sinh"

        if error is None and email:
            existing_employee = db.scalar(
                select(Employee).where(
                    Employee.email == email,
                    Employee.id != employee_id
                )
            )
            if existing_employee is not None:
                error = "Email da dc su dung"
        if error:
            departments = db.scalars(
                select(Department).order_by(Department.id)
            ).all()
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
        employee.name = name
        employee.department_id = department_id
        employee.position = position or None
        employee.phone = phone or None
        employee.email = email or None
        employee.gender = gender or None
        employee.address = address or None
        employee.birthday = birthday
        employee.start_date = start_date
        db.commit()
    return RedirectResponse(
        url = f"/employees/{employee_id}",
        status_code = 303
    )

@router.post("/employees/{employee_id}/deactivate")
def deactivate_employee(employee_id: str):
    with SessionLocal() as db:
        employee = db.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(
                status_code = 404,
                detail = "Khong tim thay nhan vien"
            )
        employee.status = "Inactive"
        db.commit()
    return RedirectResponse(
        url = f"/employees/{employee_id}",
        status_code = 303
    )
