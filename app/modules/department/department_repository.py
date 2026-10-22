from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.department.department_models import Department

def get_all_departments(db: Session):
    statement = select(Department)
    statement = statement.order_by(Department.id)

    result = db.scalars(statement)
    departments = result.all()

    return departments

def get_department_by_id(db: Session, department_id: int):
    department = db.get(Department, department_id)
    return department
def get_department_by_name(db: Session, name: str):
    statement = select(Department)
    statement = statement.where(Department.name==name)
    department = db.scalar(statement)
    return department

def add_department(db: Session, name: str):
    department = Department(name=name)
    db.add(department)
    return department
def update_department_name(department: Department, name: str):
    department.name = name