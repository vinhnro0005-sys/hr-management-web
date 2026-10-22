# Trạng thái học và tích hợp HR Management

Cập nhật: 21/10/2026. Đây là ghi chú tiếp nối, không thay thế kiểm tra code hiện tại.

## Tiến độ mới nhất — ưu tiên đọc trước các ghi chú cũ

### Sau khi người học yêu cầu lấy code B về ngày 21/10

- Đã stash toàn bộ thay đổi A (kể cả untracked) với tên Backup A refactor before integrating B auth 2026-10-21, pull fast-forward nhánh feature/a-employee-department tới bd95a80, apply lại stash và giải quyết conflict main.py. Stash vẫn giữ để phục hồi; chưa commit/push bản tích hợp.
- Người học yêu cầu KHÔNG sửa code Auth của B và giữ import của B. Chốt app/models/employee.py và department.py chỉ re-export class thật từ module. Không có hai class/table độc lập. Giữ nguyên Auth, User, seed, test B; main kết hợp session/quyền của B và validation handler của A.
- Đã cài requirements B và httpx để chạy test; thêm SESSION_SECRET_KEY ngẫu nhiên vào .env local, không in hoặc commit khóa.
- Chạy tests/test_auth_integration.py: 12 bước pass trên SQLite RAM. Thêm/chạy tests/test_employee_auth_refactor.py: create/trùng mã/edit email trống/schema lỗi giữ form/deactivate hai lần/404/model identity pass, chỉ dùng SQLite RAM.
- Đọc MySQL hiện có: kết nối được nhưng CHƯA có bảng users. Chưa chạy seed, chưa tạo tài khoản hay thay dữ liệu thật. Cần chuẩn bị User table và tài khoản trước khi người học đăng nhập được trên MySQL.
- Thiếu CSRF quản trị/logout trong code B vẫn chưa sửa theo lựa chọn người học; báo rõ trước khi coi tích hợp cuối cùng hoàn tất.

- Employee đã chuyển model vào module, tách repository/service/schema. List/search/filter, create/detail/edit/deactivate đã nối các tầng. Tên hàm ngừng hoạt động thực tế là deactive_employee, router gọi khớp; không coi tên khác hướng dẫn là lỗi chạy.
- POST create/update dùng schema; main handler trả lỗi HTML và giữ form_data; HTML sửa đã so sánh department_id theo chuỗi. Hai lỗi thụt dòng cập nhật email trống và mode/model đã sửa.
- GET sửa chuẩn bị dữ liệu ở get_employee_edit_data. Còn gom đoạn chuẩn hóa form_data lặp trong router, sau đó kiểm thử đầy đủ. Compileall app/main đã pass ngày 21/10; chưa chạy QA web/MySQL đầy đủ bản này.
- Fetch origin ngày 21/10: origin/main và origin/feature/a-employee-department cùng bd95a80 (Integrate session-based authentication); HEAD local 0d3e7cc, còn nhiều thay đổi chưa commit bao gồm refactor. Nay hai bên có chung nền 0d3e7cc; vấn đề khác gốc trước đây không còn áp dụng cho cặp HEAD/remote này.
- B đã dùng session/Jinja2/admin/employee/User.employee_id chuỗi. Chưa merge. Mô phỏng merge-file ba chiều trên bản sao cho main.py và Employee model tại đường dẫn mới đều có conflict; department list template ghép thử không conflict. Đây chưa phải mô phỏng merge toàn repo.
- Khi ghép: kết hợp SessionMiddleware/Auth dependencies của B với validation handler của A; giữ model A tại module, sửa import cũ app.models.employee/department trong Auth, models/__init__, seed và test. Không phục hồi hai model cùng bảng.
- B mới kiểm tra CSRF cho login; logout có cả GET và POST không kiểm tra CSRF, form quản trị chưa có bảo vệ CSRF. Seed có mật khẩu demo cố định và NV001 có thể trỏ nhân viên thật có sẵn. Settings mới cần SESSION_SECRET_KEY. Test B chưa được chạy ở lần review này; môi trường local cần kiểm tra dependencies test.
- Bước ngay tiếp: dạy helper chuẩn bị form_data dùng chung trong Employee router; chốt kiểm thử rồi commit local trước khi tích hợp có kiểm soát. Không tự pull/merge/force push.

## Các quyết định cần giữ

- Plan gốc: PLAN_FASTAPI_MYSQL.md. FastAPI, SQLAlchemy, MySQL và Jinja2/HTML; dùng form, render HTML và redirect.
- A phụ trách Employee/Department; B phụ trách User/Login/Role/Profile. Dùng hợp đồng dữ liệu của A, không chuyển sang JSON API theo code thử nghiệm B.
- Người học đã chọn cấu trúc module gồm models, schemas, repository, service, router. HANDOFF_B_INTEGRATION.md được viết trước quyết định tách đầy đủ này; phải đối chiếu và cập nhật cấu trúc trong handoff trước khi tích hợp, không coi nội dung cũ là quyết định mới nhất.
- Employee.id là String(20), name/start_date/status, Active/Inactive; giữ birthday/gender/phone/email/address/position/department_id. Một Base và cấu hình database chung.
- Auth đích đã chốt: session cookie, admin/employee, kiểm tra quyền phía server và CSRF khi tích hợp; B chưa được xác nhận hoàn thành.
- Người học tự viết theo bài; chỉ sửa trực tiếp khi được yêu cầu. PyCharm + GitHub Desktop. Không tự pull/merge/force push; lịch sử local main và origin/main từng khác gốc.
- Không dùng try/except trong ứng dụng theo yêu cầu người học. Exception handler vẫn là xử lý ngoại lệ framework; cần giải thích trung thực.
- Áp dụng .agents/skills/hr-project-tutor/SKILL.md: đọc code, dạy bài nhỏ, chỉ vị trí thay đổi, giải thích từng phần và ví dụ, chọn cách giảm lặp thực sự, không đổi kiến trúc liên tục.

## Trạng thái đã kiểm tra bằng đọc code

- main.py đã đăng ký Department/Employee router; chứa handler RequestValidationError cho thêm/sửa Department.
- Department có department_models/repository/schemas/service/router và list/edit templates.
- Schema tên: strip khoảng trắng, 1–100 ký tự; DepartmentUpdate kế thừa DepartmentCreate.
- Service thêm/sửa dùng schema, kiểm tra tên trùng và commit. Lỗi thụt dòng bỏ qua cập nhật tên mới đã được người học sửa; đọc lại ngày 15/10 thấy đúng.
- Form lỗi dùng entered_name; handler dịch lỗi schema và render đúng trang. Người học báo đã kiểm thử xong; chưa có bộ kiểm thử end-to-end độc lập xác nhận toàn bộ bản hiện tại.
- Employee vẫn ở app/models/employee.py; tất cả route ở app/modules/employee/employee_router.py. Chưa tách repository/service/schema Employee.
- Employee hiện có list/search q/department/status/position, create/detail/edit/deactivate; validations và giữ dữ liệu form. Trước đây đã test nhiều nhánh, không coi đó là chứng minh mọi lần refactor sau đều đúng.

## Bài tiếp theo

1. Di chuyển Employee model vào app/modules/employee/employee_models.py, sửa toàn bộ import; giữ nguyên cột và MySQL.
2. Tái sử dụng repository Department cho các dropdown thay vì viết lại truy vấn.
3. Tách repository danh sách/tìm kiếm/lọc Employee, giữ kết quả join mà HTML đang dùng. Nối vào service/router và kiểm thử hành vi.
4. Tạo schema Employee và tích hợp form + handler lỗi cùng lúc; dùng chung quy tắc create/update, giữ dữ liệu khi lỗi, không làm mất trường tùy chọn/date.
5. Tách nghiệp vụ thêm/sửa/detail/deactivate; kiểm tra tồn tại/trùng vẫn cần DB. Dọn helper email và truy vấn lặp sau khi nơi thay thế hoạt động.
6. Cập nhật handoff cho B, README/.env.example và khởi tạo DB; ghép Auth rồi kiểm thử quyền/CSRF, hoàn thiện UI/dashboard chung và demo theo plan.

Sau mỗi bài quan trọng, cập nhật trạng thái thực tế và bài tiếp theo, ghi rõ mức kiểm thử. Không lưu bí mật hoặc mật khẩu ở đây.
