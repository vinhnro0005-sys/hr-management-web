from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.department.department_models import Department
from app.modules.employee.employee_models import Employee


def get_employee_totals(db: Session):
    statement = select(
        func.count(Employee.id),
        func.count(
            case((Employee.status=="Active", 1))
        ),
        func.count(
            case((Employee.status=="Inactive", 1))
        ),
    )
    result = db.execute(statement).one()

    return result


def count_departments(db: Session):
    statement = select(func.count(Department.id))

    return db.scalar(statement)


def count_employees_by_department(db: Session):
    statement = select(
        Department.id,
        Department.name,
        func.count(Employee.id).label("employee_count"),
    )

    statement = statement.outerjoin(
        Employee,
        Department.id == Employee.department_id
    )

    statement = statement.group_by(
        Department.id,
        Department.name
    )

    statement = statement.order_by(Department.name)
    return db.execute(statement).all()
