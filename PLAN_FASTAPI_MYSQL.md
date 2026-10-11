# KẾ HOẠCH PHÁT TRIỂN WEBSITE QUẢN LÝ NHÂN SỰ

**Công nghệ chính:** Python + FastAPI + MySQL + SQLAlchemy + HTML/CSS/Bootstrap + Jinja2  
**Nhóm:** 2 người  
**Timeline:** 5 tuần

---

# 1. Tổng quan dự án

## 1.1. Mục tiêu

Xây dựng một **website quản lý nhân sự** hỗ trợ doanh nghiệ thông tin nhân viên thông qua gip quản lý tập trungao diện web.

Website cho phép:

- Quản lý thông tin nhân viên.
- Quản lý phòng ban.
- Thêm, sửa, xóa hoặc ngừng hoạt động nhân viên.
- Tìm kiếm và lọc nhân viên.
- Đăng nhập vào hệ thống.
- Phân quyền giữa tài khoản quản trị và tài khoản nhân viên.
- Hiển thị một số thống kê nhân sự cơ bản.

Backend sử dụng **FastAPI**, dữ liệu được lưu trên **MySQL**, Python làm việc với database thông qua **SQLAlchemy**.

---

# 2. Phạm vi chức năng

## 2.1. Chức năng bắt buộc

### Quản lý nhân viên

- Xem danh sách nhân viên.
- Thêm nhân viên.
- Sửa thông tin nhân viên.
- Xóa hoặc chuyển nhân viên sang trạng thái không hoạt động.
- Xem chi tiết nhân viên.
- Tìm kiếm theo mã hoặc tên.
- Lọc theo phòng ban.
- Lọc theo chức vụ.
- Validation dữ liệu.

### Quản lý phòng ban

- Xem danh sách phòng ban.
- Thêm phòng ban.
- Sửa phòng ban.
- Gán nhân viên vào phòng ban.

### Đăng nhập

- Tài khoản quản trị.
- Tài khoản nhân viên.
- Đăng nhập.
- Đăng xuất.
- Kiểm tra mật khẩu.

### Phân quyền

**Admin:**
- Quản lý nhân viên.
- Quản lý phòng ban.
- Xem toàn bộ danh sách nhân viên.

**Employee:**
- Đăng nhập.
- Xem thông tin cá nhân.
- Không được sử dụng các chức năng quản trị.

---

# 3. Chức năng nên có

- Dashboard.
- Tổng số nhân viên.
- Tổng số phòng ban.
- Thống kê nhân viên theo phòng ban.
- Thống kê nhân viên đang làm / đã nghỉ.
- Tìm kiếm nhanh.
- Thông báo sau khi thêm, sửa hoặc xóa.
- Responsive cơ bản.

---

# 4. Chức năng mở rộng

Nếu còn thời gian có thể bổ sung:

- Chấm công.
- Tính lương.
- Export Excel.
- Pagination.
- Đổi mật khẩu.
- Quản lý tài khoản nâng cao.
- Biểu đồ Dashboard.
- REST API cho frontend/mobile khác.

**Chấm công và tính lương không nằm trong MVP hiện tại.**

---

# 5. Kiến trúc tổng thể

```text
NGƯỜI DÙNG
    │
    ▼
TRÌNH DUYỆT
    │
    │ HTTP Request
    ▼
FASTAPI ROUTER
    │
    ▼
SERVICE LAYER
    │
    ▼
SQLALCHEMY
    │
    ▼
MYSQL
    │
    ▼
JINJA2 TEMPLATE
    │
    ▼
HTML + CSS + BOOTSTRAP
    │
    ▼
TRÌNH DUYỆT
```

Ví dụ khi thêm nhân viên:

```text
Form HTML
    ↓
POST /employees/create
    ↓
FastAPI Router
    ↓
Validation
    ↓
Employee Service
    ↓
SQLAlchemy
    ↓
MySQL
    ↓
Redirect về danh sách nhân viên
```

---

# 6. Vai trò từng công nghệ

| Công nghệ | Vai trò |
|---|---|
| Python | Xử lý logic nghiệp vụ |
| FastAPI | Backend, routes và REST API |
| MySQL | Lưu dữ liệu hệ thống |
| SQLAlchemy | ORM kết nối Python với MySQL |
| Jinja2 | Render dữ liệu Python vào HTML |
| HTML | Xây dựng cấu trúc giao diện |
| CSS | Tùy chỉnh giao diện |
| Bootstrap | Làm giao diện nhanh và responsive |
| JavaScript | Chỉ dùng khi thực sự cần tương tác phía client |

---

# 7. Cấu trúc file mục tiêu

```text
hr_management_web/
│
├── main.py
├── requirements.txt
├── README.md
├── PLAN.md
├── .gitignore
├── .env
│
├── app/
│   │
│   ├── database.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── employee.py
│   │   ├── department.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── employee_schema.py
│   │   ├── department_schema.py
│   │   └── user_schema.py
│   │
│   ├── services/
│   │   ├── employee_service.py
│   │   ├── department_service.py
│   │   └── auth_service.py
│   │
│   ├── routers/
│   │   ├── main_router.py
│   │   ├── employee_router.py
│   │   ├── department_router.py
│   │   └── auth_router.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   │
│   │   ├── employees/
│   │   │   ├── list.html
│   │   │   ├── form.html
│   │   │   └── detail.html
│   │   │
│   │   ├── departments/
│   │   │   ├── list.html
│   │   │   └── form.html
│   │   │
│   │   └── profile/
│   │       └── profile.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   │
│   └── utils/
│       ├── validators.py
│       ├── security.py
│       └── constants.py
│
├── tests/
│   ├── test_employee.py
│   ├── test_department.py
│   └── test_auth.py
│
└── seed.py
```

---

# 8. Vai trò file quan trọng

## `main.py`

Khởi động FastAPI:

```text
uvicorn main:app --reload
```

## `database.py`

Thiết lập kết nối:

```text
FastAPI
   ↓
SQLAlchemy
   ↓
MySQL
```

## `models/`

Mô tả các bảng MySQL.

## `schemas/`

Dùng Pydantic để kiểm tra dữ liệu request/response.

Ví dụ:

```text
EmployeeCreate
EmployeeUpdate
EmployeeResponse
```

## `services/`

Chứa logic nghiệp vụ.

Ví dụ:

```text
create_employee()
update_employee()
search_employee()
authenticate_user()
```

## `routers/`

Định nghĩa endpoint:

```text
/employees
/departments
/login
/logout
/profile
```

## `templates/`

HTML/Jinja2.

## `static/`

CSS, JS, hình ảnh.

## `.env`

Lưu thông tin nhạy cảm:

```text
DB_HOST
DB_USER
DB_PASSWORD
DB_NAME
SECRET_KEY
```

**Không commit `.env` lên GitHub.**

---

# 9. Database

## 9.1. `departments`

| Field | Type | Constraint |
|---|---|---|
| id | INT | PRIMARY KEY, AUTO_INCREMENT |
| name | VARCHAR | NOT NULL, UNIQUE |

## 9.2. `employees`

| Field | Type | Constraint |
|---|---|---|
| id | VARCHAR | PRIMARY KEY |
| name | VARCHAR | NOT NULL |
| birthday | DATE | |
| gender | VARCHAR | |
| phone | VARCHAR | |
| email | VARCHAR | UNIQUE |
| address | VARCHAR | |
| position | VARCHAR | |
| department_id | INT | FOREIGN KEY |
| start_date | DATE | |
| status | VARCHAR | Active / Inactive |

Quan hệ:

```text
DEPARTMENT
     │
     │ 1:N
     ▼
EMPLOYEE
```

## 9.3. `users`

| Field | Type | Constraint |
|---|---|---|
| id | INT | PRIMARY KEY |
| username | VARCHAR | UNIQUE |
| password_hash | VARCHAR | NOT NULL |
| role | VARCHAR | ADMIN / EMPLOYEE |
| employee_id | VARCHAR | FOREIGN KEY |

Quan hệ:

```text
EMPLOYEE
    │
    │ 1:1
    ▼
USER
```

Không lưu mật khẩu dạng plain text mà lưu password hash.

---

# 10. Business Rules

## Employee

- ID không được trùng.
- Tên không được rỗng.
- Email không được trùng.
- Email phải đúng định dạng.
- Phòng ban phải tồn tại.
- Nhân viên nghỉ việc chuyển thành `Inactive`.
- Không xóa dữ liệu lịch sử không cần thiết.

## Department

- Tên phòng ban không được trùng.
- Không cho gán nhân viên vào phòng ban không tồn tại.

## User

- Username không được trùng.
- Mật khẩu không lưu dạng plain text.
- User phải có role.
- Employee không được truy cập trang Admin.

---

# 11. Authentication Flow

```text
Người dùng nhập
Username + Password
       ↓
POST /login
       ↓
FastAPI
       ↓
Tìm user trong MySQL
       ↓
Kiểm tra password hash
       ↓
      Đúng?
      /   \
    Có     Không
     ↓       ↓
Session   Báo lỗi
     ↓
Dashboard/Profile
```

---

# 12. Authorization Flow

```text
GET /employees
      ↓
User đã login?
      ↓
role == ADMIN?
   /        \
 Có          Không
 ↓             ↓
Cho xem      403 / redirect
```

---

# 13. Thứ tự ưu tiên

| Mức | Chức năng |
|---|---|
| MUST | Employee CRUD, Department, MySQL, Login, Role |
| SHOULD | Search, Filter, Validation, Profile |
| COULD | Dashboard, Chart, Pagination |
| OPTIONAL | Attendance, Salary, Excel |

---

# 14. Dependency module

```text
MYSQL / SQLALCHEMY
        ↓
DEPARTMENT
        ↓
EMPLOYEE
        ↓
USER
        ↓
LOGIN
        ↓
ROLE
        ↓
DASHBOARD
```

---

# 15. Kế hoạch phát triển — 5 tuần

# Sprint 1 — Foundation

**Tuần 1**

- [ ] Tạo GitHub repository.
- [ ] Mời collaborator.
- [ ] Tạo `.gitignore`.
- [ ] Tạo `.env`.
- [ ] Tạo `requirements.txt`.
- [ ] Cài FastAPI.
- [ ] Cài Uvicorn.
- [ ] Cài SQLAlchemy.
- [ ] Cài MySQL driver.
- [ ] Kết nối FastAPI → MySQL.
- [ ] Tạo project structure.
- [ ] Tạo `base.html`.
- [ ] Kết nối Bootstrap.
- [ ] Tạo Department model.
- [ ] Tạo Employee model.
- [ ] Tạo trang `/employees`.

### Output

```text
uvicorn main:app --reload
```

Website chạy và lấy được dữ liệu MySQL.

---

# Sprint 2 — Employee & Department

**Tuần 2**

### Department

- [ ] Danh sách phòng ban.
- [ ] Thêm.
- [ ] Sửa.
- [ ] Chặn duplicate.

### Employee

- [ ] Danh sách.
- [ ] Thêm.
- [ ] Sửa.
- [ ] Deactivate.
- [ ] Detail.
- [ ] Search theo ID.
- [ ] Search theo tên.
- [ ] Filter phòng ban.
- [ ] Filter chức vụ.
- [ ] Filter Active/Inactive.
- [ ] Validation.

### Milestone 1

- [ ] CRUD chạy.
- [ ] Search chạy.
- [ ] Filter chạy.
- [ ] Department liên kết Employee.
- [ ] MySQL persistent.

---

# Sprint 3 — Login & Role

**Tuần 3**

- [ ] Tạo User model.
- [ ] Tạo user schema.
- [ ] Tạo login form.
- [ ] Hash password.
- [ ] Verify password.
- [ ] Login.
- [ ] Logout.
- [ ] Session hoặc cơ chế authentication phù hợp.
- [ ] Admin role.
- [ ] Employee role.
- [ ] Chặn Employee truy cập Admin page.
- [ ] Profile nhân viên.

### Milestone 2

```text
Admin
→ quản lý nhân viên

Employee
→ chỉ xem profile
```

---

# Sprint 4 — Dashboard & Integration

**Tuần 4**

- [ ] Dashboard.
- [ ] Tổng nhân viên.
- [ ] Tổng phòng ban.
- [ ] Active / Inactive.
- [ ] Nhân viên theo phòng.
- [ ] Navigation.
- [ ] Navbar/sidebar.
- [ ] Notification.
- [ ] Error page.
- [ ] Responsive.
- [ ] Test Employee → Department.
- [ ] Test Employee → User.
- [ ] Test Login → Role.

### Milestone 3 — MVP

- [ ] Employee.
- [ ] Department.
- [ ] Login.
- [ ] Role.
- [ ] Profile.
- [ ] Search/Filter.
- [ ] MySQL.
- [ ] Dashboard cơ bản.

---

# Sprint 5 — Testing & Release

**Tuần 5**

- [ ] Test toàn bộ chức năng.
- [ ] Fix bug.
- [ ] Test database mới.
- [ ] Test trên máy cả hai người.
- [ ] Test account Admin.
- [ ] Test account Employee.
- [ ] Test permission.
- [ ] Test validation.
- [ ] Tạo dữ liệu demo.
- [ ] Hoàn thiện README.
- [ ] Hoàn thiện UI.
- [ ] Chuẩn bị demo.
- [ ] Chuẩn bị báo cáo.
- [ ] Chuẩn bị thuyết trình.
- [ ] Review code cuối.

Nếu còn thời gian:

- [ ] Pagination.
- [ ] Chart.
- [ ] Export Excel.
- [ ] Attendance.

---

# 16. Testing Plan

| Test | Thao tác | Expected |
|---|---|---|
| Duplicate ID | Tạo cùng Employee ID | Báo lỗi |
| Empty name | Không nhập tên | Không lưu |
| Duplicate email | Dùng email đã tồn tại | Báo lỗi |
| Department invalid | Department không tồn tại | Không lưu |
| Duplicate username | Tạo username giống nhau | Báo lỗi |
| Wrong password | Login sai password | Không login |
| Employee access admin | Employee mở `/employees` admin | Bị chặn |
| Admin access | Admin mở Employee Management | Cho phép |
| Search no result | Search tên không tồn tại | Empty state |
| Restart server | Restart FastAPI | Dữ liệu MySQL còn |
| Invalid form | Input sai | Không crash |
| Inactive | Deactivate employee | Lịch sử còn |

---

# 17. Git Workflow

```text
main
├── feature/employee
├── feature/department
├── feature/auth
├── feature/dashboard
├── feature/frontend
└── fix/...
```

Quy trình:

```text
Pull main
   ↓
Create branch
   ↓
Code
   ↓
Test
   ↓
Commit
   ↓
Push
   ↓
Pull Request
   ↓
Review
   ↓
Merge
```

---

# 18. Phân chia 2 người

## Việc chung

- Thiết kế database.
- Setup FastAPI.
- Setup MySQL.
- Kiến trúc project.
- `base.html`.
- Dashboard.
- Integration.
- Testing.
- README.
- Báo cáo.
- Demo.

## Người 1 — Employee & Department

Phụ trách:

```text
models/
    employee.py
    department.py

schemas/
    employee_schema.py
    department_schema.py

services/
    employee_service.py
    department_service.py

routers/
    employee_router.py
    department_router.py
```

Frontend:

```text
templates/employees/
templates/departments/
```

Chức năng:

- Employee CRUD.
- Department CRUD.
- Search.
- Filter.
- Validation.
- Active/Inactive.

## Người 2 — Login & Authorization

Phụ trách:

```text
models/user.py
schemas/user_schema.py
services/auth_service.py
routers/auth_router.py
utils/security.py
```

Frontend:

```text
login.html
profile/profile.html
```

Chức năng:

- User.
- Password hash.
- Login.
- Logout.
- Admin role.
- Employee role.
- Permission.
- Profile.

Hỗ trợ:

- MySQL setup.
- Dashboard statistics.
- Testing Employee.

---

# 19. Demo Flow

```text
1. Login Admin
      ↓
2. Tạo Department
      ↓
3. Thêm Employee
      ↓
4. Search / Filter
      ↓
5. Edit Employee
      ↓
6. Xem Dashboard
      ↓
7. Logout
      ↓
8. Login Employee
      ↓
9. Xem Profile
      ↓
10. Thử truy cập Admin page
      ↓
11. Hệ thống từ chối
```

Flow này thể hiện được:

**CRUD + FastAPI + MySQL + Authentication + Authorization.**

---

# 20. MVP cuối cùng

Bản tối thiểu để nộp:

```text
FastAPI
   ↓
MySQL
   ↓
SQLAlchemy

Department CRUD
      ↓
Employee CRUD
      ↓
Search / Filter
      ↓
Login
      ↓
Admin / Employee Role
      ↓
Profile
```

Nếu toàn bộ phần này chạy ổn thì project đã đủ thành một **Web Quản lý Nhân sự hoàn chỉnh ở quy mô nhỏ**.
