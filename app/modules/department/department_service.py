from sqlalchemy.orm import Session

from app.modules.department.department_models import Department
from app.modules.department.department_repository import (
    add_department,
    get_department_by_name,
    get_employee_by_department_id,
    remove_department,
    update_department_name,
)
from app.modules.department.department_schemas import DepartmentCreate, DepartmentUpdate


def create_department(db: Session, data: DepartmentCreate):
    existing_department = get_department_by_name(db, data.name)
    if existing_department:
        return "Tên phòng ban đã tồn tại"

    add_department(db, data.name)
    db.commit()

    return None


def update_department(
        db: Session,
        department: Department,
        data: DepartmentUpdate,
):
    existing_department = get_department_by_name(db, data.name)
    if existing_department:
        if existing_department.id != department.id:
            return "Tên phòng ban đã tồn tại"

    update_department_name(department, data.name)
    db.commit()
    return None


def delete_department(db: Session, department: Department):
    existing_employee = get_employee_by_department_id(db, department.id)
    if existing_employee:
        return "Không thể xóa phòng ban đang có nhân viên"

    remove_department(db, department)
    db.commit()
    return None
