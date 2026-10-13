import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.modules.auth.auth_service import AuthService


def seed():
    print("--- Khởi tạo cơ sở dữ liệu và tài khoản mẫu ---")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # 1. Tạo phòng ban mẫu nếu chưa có
        dept = db.scalar(select(Department).where(Department.name == "Phòng Công nghệ thông tin"))
        if dept is None:
            dept = Department(name="Phòng Công nghệ thông tin")
            db.add(dept)
            db.commit()
            db.refresh(dept)
            print(" -> Đã tạo phòng ban: Phòng Công nghệ thông tin (ID:", dept.id, ")")
        else:
            print(" -> Phòng ban đã tồn tại (ID:", dept.id, ")")

        # 2. Tạo nhân viên mẫu nếu chưa có
        emp = db.get(Employee, "NV001")
        if emp is None:
            emp = Employee(
                id="NV001",
                name="Nguyễn Văn A",
                department_id=dept.id,
                position="Lập trình viên",
                email="nguyenvana@example.com",
                phone="0901234567",
                gender="Nam",
                address="Hà Nội",
                status="Active",
            )
            db.add(emp)
            db.commit()
            db.refresh(emp)
            print(" -> Đã tạo nhân viên mẫu: NV001 - Nguyễn Văn A")
        else:
            print(" -> Nhân viên NV001 đã tồn tại")

        # 3. Tạo tài khoản admin mẫu nếu chưa có
        admin_user = db.scalar(select(User).where(User.username == "admin"))
        if admin_user is None:
            admin_user, err = AuthService.create_user(
                db=db,
                username="admin",
                password="admin123",
                role="admin",
            )
            if err:
                print(" -> Lỗi tạo tài khoản admin:", err)
            else:
                print(" -> Đã tạo tài khoản admin: username='admin', password='admin123'")
        else:
            print(" -> Tài khoản admin đã tồn tại (giữ nguyên mật khẩu cũ)")

        # 4. Tạo tài khoản employee mẫu nếu chưa có
        emp_user = db.scalar(select(User).where(User.username == "employee"))
        if emp_user is None:
            emp_user, err = AuthService.create_user(
                db=db,
                username="employee",
                password="employee123",
                role="employee",
                employee_id="NV001",
            )
            if err:
                print(" -> Lỗi tạo tài khoản employee:", err)
            else:
                print(" -> Đã tạo tài khoản employee: username='employee', password='employee123' (gắn với NV001)")
        else:
            print(" -> Tài khoản employee đã tồn tại (giữ nguyên mật khẩu cũ)")

    print("--- Hoàn tất quá trình seed! ---")


if __name__ == "__main__":
    seed()
