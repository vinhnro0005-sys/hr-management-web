"""Kiểm tra refactor Employee sau khi ghép Auth, chỉ dùng SQLite trong RAM."""

import re

from test_auth_integration import test_auth_full_flow as reset_and_check_auth


def test_employee_auth_refactor():
    # Bộ test B khởi tạo DB thử và gắn SessionLocal trước khi import ứng dụng.
    reset_and_check_auth()

    from fastapi.testclient import TestClient
    from app.database import SessionLocal
    from app.models.employee import Employee
    from app.modules.employee.employee_models import Employee as ModuleEmployee
    from main import app

    assert Employee is ModuleEmployee

    client = TestClient(app, follow_redirects=False)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    login = client.post("/login", data={
        "username": "admin",
        "password": "admin123",
        "csrf_token": token,
    })
    assert login.status_code == 303

    form_page = client.get("/employees/create")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', form_page.text).group(1)

    with SessionLocal() as db:
        department_id = db.get(Employee, "NV001").department_id

    data = {
        "csrf_token": csrf,
        "id": "TEST_REFACTOR",
        "name": "Test refactor",
        "department_id": str(department_id),
        "email": "",
        "birthday": "",
        "start_date": "",
    }
    created = client.post("/employees/create", data=data)
    assert created.status_code == 200
    assert "credential-panel" in created.text
    duplicate = client.post("/employees/create", data=data)
    assert duplicate.status_code == 400
    assert 'value="TEST_REFACTOR"' in duplicate.text

    data["name"] = "Updated without email"
    assert client.post("/employees/TEST_REFACTOR/edit", data=data).status_code == 303
    with SessionLocal() as db:
        employee = db.get(Employee, "TEST_REFACTOR")
        assert employee.name == "Updated without email"
        assert employee.email is None

    data["birthday"] = "2999-01-01"
    invalid = client.post("/employees/TEST_REFACTOR/edit", data=data)
    assert invalid.status_code == 400
    assert 'value="Updated without email"' in invalid.text
    assert re.search(r'value="' + str(department_id) + r'"\s+selected', invalid.text)

    assert client.get("/employees/TEST_REFACTOR/edit").status_code == 200
    assert client.post("/employees/TEST_REFACTOR/deactivate", data={"csrf_token": csrf}).status_code == 303
    assert client.post("/employees/TEST_REFACTOR/deactivate", data={"csrf_token": csrf}).status_code == 303
    assert client.post("/employees/TEST_REFACTOR/deactivate").status_code == 403
    with SessionLocal() as db:
        assert db.get(Employee, "TEST_REFACTOR").status == "Inactive"

    assert client.get("/employees/DOES_NOT_EXIST").status_code == 404
    print("EMPLOYEE + AUTH REFACTOR CHECKS PASSED (in-memory SQLite)")


if __name__ == "__main__":
    test_employee_auth_refactor()
