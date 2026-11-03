import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.auth.auth_service import AuthService
from app.modules.auth.security import hash_password
from app.modules.department.department_repository import (
    get_all_departments,
    get_department_by_id,
)
from app.modules.employee.employee_models import Employee
from app.modules.employee.employee_repository import (
    add_employee,
    get_employee_by_email,
    get_employee_by_id,
    get_employee_position,
    search_employees,
    update_employee_fields,
    get_all_employee_ids,
    get_user_by_employee_id,
)
from app.modules.employee.employee_schemas import (
    EmployeeCreate,
    EmployeeUpdate,
)

def get_employee_list_data(
    db: Session,
    q: str = "",
    department_id: str = "",
    status: str = "",
    position: str = ""
):
    q = q.strip()
    departments = get_all_departments(db)
    positions = get_employee_position(db)

    valid_department_ids = set()

    for department in departments:
        valid_department_ids.add(str(department.id))

    if department_id not in valid_department_ids:
        department_id = ""
    if status not in ("", "Active", "Inactive"):
        status = ""
    if position not in positions:
        position = ""
    department_id_value = None

    if department_id:
        department_id_value = int(department_id)

    employees = search_employees(
        db=db,
        q=q,
        department_id=department_id_value,
        status=status,
        position=position,
    )
    return {
        "employees": employees,
        "q": q,
        "departments": departments,
        "positions": positions,
        "selected_department": department_id,
        "selected_position": position,
        "selected_status": status,
    }


def create_employee(db: Session, data: EmployeeCreate):
    department = get_department_by_id(db, data.department_id)

    if department is None:
        return None, {"field": "department_id", "message": "Phòng ban không tồn tại"}
    existing_employee = get_employee_by_email(db, data.email)
    if existing_employee is not None:
        return None, {"field": "email", "message": "Email đã được sử dụng"}

    username = generate_employee_id(db)

    initial_password = secrets.token_urlsafe(12)
    password_hash = hash_password(initial_password)

    employee = Employee(
        id=username,
        name=data.name,
        department_id=data.department_id,
        position=data.position,
        phone=data.phone,
        email=data.email,
        gender=data.gender,
        address=data.address,
        birthday=data.birthday,
        start_date=data.start_date,
        status="Active",
    )
    add_employee(db, employee)
    db.flush()

    user = User(
        username=username,
        password_hash=password_hash,
        role="employee",
        employee_id=employee.id,
        is_active=True,
    )

    db.add(user)

    db.commit()

    credentials = {
        "username": username,
        "initial_password": initial_password
    }
    return credentials, None


def get_employee_detail_data(db: Session, employee_id: str):
    employee = get_employee_by_id(db, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nhân viên",
        )
    department = get_department_by_id(
        db,
        employee.department_id,
    )

    return {
        "employee": employee,
        "department": department,
    }


def update_employee(
        db: Session,
        employee: Employee,
        data: EmployeeUpdate,
):
    department = get_department_by_id(db, data.department_id)

    if department is None:
        return {"field": "department_id", "message": "Phòng ban không tồn tại"}

    existing_employee = get_employee_by_email(db, data.email)

    if existing_employee is not None:
        if existing_employee.id != employee.id:
            return {"field": "email", "message": "Email đã được sử dụng"}

    values = data.model_dump()
    update_employee_fields(employee, values)
    db.commit()
    return None


def get_employee_edit_data(db: Session, employee_id: str):
    employee = get_employee_by_id(db, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nhân viên",
        )

    departments = get_all_departments(db)

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
    for field_name, value in form_data.items():
        if value is None:
            form_data[field_name] = ""

    if employee.birthday is not None:
        form_data["birthday"] = employee.birthday.isoformat()
    if employee.start_date is not None:
        form_data["start_date"] = employee.start_date.isoformat()

    return {
        "employee": employee,
        "departments": departments,
        "form_data": form_data,
    }


def deactivate_employee(db: Session, employee_id: str):
    employee = get_employee_by_id(db, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nhân viên",
        )
    if employee.status == "Inactive":
        return
    update_employee_fields(
        employee,
        {"status": "Inactive"}
    )
    user = get_user_by_employee_id(db, employee.id)
    if user is not None:
        user.is_active = False

    db.commit()

def activate_employee(db: Session, employee_id: str):
    employee = get_employee_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy nhân viên",
        )
    if employee.status == "Active":
        return
    update_employee_fields(
        employee,
        {"status": "Active"}
    )
    user = get_user_by_employee_id(db, employee.id)
    if user is not None:
        user.is_active = True
    db.commit()

def generate_employee_id(db: Session) -> str:
    employee_ids = get_all_employee_ids(db)
    max_number = 0
    for emp_id in employee_ids:
        if emp_id.startswith("NV"):
            number_part = emp_id[2:]
            if number_part.isdigit():
                number = int(number_part)
                if number > max_number:
                    max_number = number
    next_number = max_number + 1
    new_id = f"NV{next_number:03d}"

    while AuthService.get_user_by_username(db, new_id) is not None:
        next_number += 1
        new_id = f"NV{next_number:03d}"
    return new_id