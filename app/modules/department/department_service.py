from sqlalchemy.orm import Session

from app.modules.department.department_models import Department
from app.modules.department.department_repository import (
    get_department_by_name,
    add_department,
    update_department_name
)
from app.modules.department.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate
)

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