from sqlalchemy.orm import Session
from app.modules.dashboard.dashboard_repository import (
        get_employee_totals,
        count_departments,
        count_employees_by_department,
)

def get_dashboard_data(db: Session):
    totals = get_employee_totals(db)

    total_employees, active_employees, inactive_employees = totals
    total_departments = count_departments(db)
    department_statistics = count_employees_by_department(db)

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_departments": total_departments,
        "department_statistics": department_statistics
    }