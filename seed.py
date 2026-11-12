import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select, text

from app.core.database import Base, SessionLocal, engine
from app.modules.department.department_models import Department
from app.modules.employee.employee_models import Employee
from app.modules.auth.auth_models import User
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
                position="Chuyên viên",
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

        # 5. Tạo View v_hr_analytics phục vụ Chatbot Text2SQL
        try:
            view_sql = """
            CREATE OR REPLACE VIEW v_hr_analytics AS
            SELECT 
                e.id AS id,
                e.name AS name,
                e.gender AS gender,
                e.birthday AS birthday,
                e.phone AS phone,
                e.email AS email,
                e.address AS address,
                e.position AS position,
                d.name AS department,
                e.start_date AS start_date,
                e.status AS status
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id;
            """
            if engine.dialect.name == "sqlite":
                db.execute(text("DROP VIEW IF EXISTS v_hr_analytics"))
                view_sql = view_sql.replace("CREATE OR REPLACE VIEW", "CREATE VIEW").rstrip(";")
            db.execute(text(view_sql))
            db.commit()
            print(" -> Đã tạo View phân tích dữ liệu cho AI Chatbot: v_hr_analytics")
        except Exception as ex:
            print(" -> Cảnh báo khi tạo View v_hr_analytics:", ex)

    print("--- Hoàn tất quá trình seed! ---")


if __name__ == "__main__":
    seed()
