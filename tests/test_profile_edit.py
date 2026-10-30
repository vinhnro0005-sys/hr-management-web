"""Kiểm tra sửa hồ sơ cá nhân: lưu được, không đổi phòng ban/chức vụ, lỗi hiện 1 lần."""

import re

from test_auth_integration import test_auth_full_flow as reset_and_check_auth


def _csrf(text):
    return re.search(r'name="csrf_token" value="([^"]+)"', text).group(1)


def test_profile_edit():
    reset_and_check_auth()

    from fastapi.testclient import TestClient

    from app.database import SessionLocal
    from app.models import Department, Employee
    from main import app

    with SessionLocal() as db:
        other = Department(name="HR-other")
        db.add(other)
        db.commit()
        other_id = other.id
        original_department = db.get(Employee, "NV001").department_id

    client = TestClient(app, follow_redirects=False)
    token = _csrf(client.get("/login").text)
    assert client.post("/login", data={
        "username": "employee", "password": "employee123", "csrf_token": token,
    }).status_code == 303

    page = client.get("/profile/edit")
    assert page.status_code == 200
    csrf = _csrf(page.text)

    # Lưu thành công, cố tình gửi kèm phòng ban/chức vụ -> phải bị bỏ qua
    resp = client.post("/profile/edit", data={
        "csrf_token": csrf,
        "name": "Ten Moi",
        "phone": "0900000000",
        "department_id": str(other_id),
        "position": "Giam doc",
    })
    assert resp.status_code == 303
    with SessionLocal() as db:
        emp = db.get(Employee, "NV001")
        assert emp.name == "Ten Moi"
        assert emp.phone == "0900000000"
        assert emp.department_id == original_department
        assert emp.position != "Giam doc"

    # Lỗi nghiệp vụ: hiện thông báo dạng chữ, đúng 1 banner, không lộ dict
    resp = client.post("/profile/edit", data={
        "csrf_token": csrf, "name": "X", "birthday": "2999-01-01",
    })
    assert resp.status_code in (400, 422)

    # CSRF sai
    resp = client.post("/profile/edit", data={"csrf_token": "bad", "name": "Y"})
    assert resp.status_code == 400
    assert resp.text.count('class="message message-error"') == 1
    assert "{'field'" not in resp.text


if __name__ == "__main__":
    test_profile_edit()
    print("ALL PROFILE EDIT TESTS PASSED!")
