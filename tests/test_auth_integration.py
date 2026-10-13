import os
import re
import sys

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database
from app.database import Base
from app.models import Department, Employee
from app.modules.auth.auth_service import AuthService


def test_auth_full_flow():
    # Use in-memory SQLite for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)

    app.database.engine = test_engine
    app.database.SessionLocal = TestSession

    from main import app as test_app

    with TestSession() as db:
        d = Department(name="IT")
        db.add(d)
        db.commit()

        e = Employee(id="NV001", name="Nguyen Van A", department_id=d.id, status="Active")
        db.add(e)
        db.commit()

        AuthService.create_user(db, "admin", "admin123", role="admin")
        AuthService.create_user(db, "employee", "employee123", role="employee", employee_id="NV001")

    client = TestClient(test_app, follow_redirects=False)

    # 1. Root redirect unauthenticated -> /login
    res = client.get("/")
    assert res.status_code == 303
    assert res.headers["location"] == "/login"

    # 2. Unauthenticated access to /employees -> redirect to /login
    res = client.get("/employees")
    assert res.status_code == 303
    assert res.headers["location"] == "/login"

    # 3. GET /login returns 200 with HTML
    res = client.get("/login")
    assert res.status_code == 200
    assert "Đăng nhập" in res.text

    match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
    assert match is not None
    csrf_token = match.group(1)

    # 4. POST /login with invalid password -> 400
    res = client.post("/login", data={"username": "admin", "password": "wrongpassword", "csrf_token": csrf_token})
    assert res.status_code == 400
    assert "không chính xác" in res.text

    match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
    assert match is not None
    csrf_token = match.group(1)

    # 5. POST /login as admin -> redirect /employees
    res = client.post("/login", data={"username": "admin", "password": "admin123", "csrf_token": csrf_token})
    assert res.status_code == 303
    assert res.headers["location"] == "/employees"

    # 6. Admin can access /employees
    res = client.get("/employees")
    assert res.status_code == 200
    assert "Danh sách nhân viên" in res.text

    # 7. Admin logout -> redirect to /login
    res = client.post("/logout")
    assert res.status_code == 303
    assert res.headers["location"] == "/login"

    # 8. Access /employees after logout -> redirect to /login
    res = client.get("/employees")
    assert res.status_code == 303
    assert res.headers["location"] == "/login"

    # 9. Login as employee
    res = client.get("/login")
    match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
    assert match is not None
    csrf_token = match.group(1)

    res = client.post("/login", data={"username": "employee", "password": "employee123", "csrf_token": csrf_token})
    assert res.status_code == 303
    assert res.headers["location"] == "/profile"

    # 10. Employee accesses /profile -> 200
    res = client.get("/profile")
    assert res.status_code == 200
    assert "NV001" in res.text
    assert "Nguyen Van A" in res.text

    # 11. Employee accesses admin page /employees -> 403 Forbidden
    res = client.get("/employees")
    assert res.status_code == 403

    # 12. Employee accesses admin page /departments -> 403 Forbidden
    res = client.get("/departments")
    assert res.status_code == 403

    print("ALL 12 INTEGRATION TESTS PASSED PERFECTLY!")


if __name__ == "__main__":
    test_auth_full_flow()
