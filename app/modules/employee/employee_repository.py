from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.modules.employee.employee_models import Employee
from app.modules.department.department_models import Department



def get_employee_position(db: Session):
    statement = select(Employee.position)
    statement = statement.where(
        Employee.position.is_not(None),
        Employee.position != "",
    )
    statement = statement.distinct()
    statement = statement.order_by(Employee.position)

    positions = db.scalars(statement).all()

    return positions

def search_employees(
        db: Session,
        q: str = "",
        department_id: int | None = None,
        status: str = "",
        position: str = ""
):
    statement = select(Employee, Department.name)
    statement = statement.join(
        Department,
        Employee.department_id == Department.id
    )

    if q:
        statement = statement.where(
            or_(
                Employee.id.contains(q, autoescape=True),
                Employee.name.contains(q, autoescape=True),
            )
        )

    if department_id is not None:
        statement = statement.where(
            Employee.department_id == department_id
        )

    if status:
        statement = statement.where(Employee.status == status)
    if position:
        statement = statement.where(Employee.position == position)
    statement = statement.order_by(Employee.id)
    employees = db.execute(statement).all()
    return employees


def get_employee_by_id(
        db: Session,
        employee_id: str
):
    return db.get(Employee, employee_id)

def get_employee_by_email(
        db: Session,
        email: str
):
    statement = select(Employee).where(Employee.email == email)
    return db.scalar(statement)

def add_employee(db: Session, employee: Employee):
    db.add(employee)

def update_employee_fields(employee: Employee, values: dict):
    for field_name, value in values.items():
        setattr(employee, field_name, value)