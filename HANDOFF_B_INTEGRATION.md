# Hướng dẫn B chỉnh sửa và tích hợp với phần A

> Cập nhật tích hợp 21/10/2026: B đã có commit bd95a80, đã được lấy về máy A và ghép với refactor. Quyết định mới nhất: giữ nguyên code/import Auth của B; app/models/employee.py và department.py dẫn lại class thật trong app/modules để hai bên dùng cùng một model. main.py giữ cả session/quyền và handler form. Test Auth và Employee trên SQLite RAM đã pass; MySQL local A chưa có bảng users/tài khoản. Bản ghép chưa commit/push. Các phần cấu trúc và yêu cầu chỉnh sửa bên dưới là tài liệu ban đầu; đọc cùng PROJECT_PROGRESS.md để tránh làm ngược quyết định mới nhất.

Ngày chốt: 11/10/2026.

## 1. Quyết định chung — dùng phần A làm chuẩn

Tài liệu này chốt hướng tích hợp theo yêu cầu của A và `PLAN_FASTAPI_MYSQL.md`. Đây là yêu cầu cần thực hiện, không phải xác nhận code B đã đáp ứng.

- Sản phẩm là website FastAPI + SQLAlchemy + MySQL + HTML/Bootstrap/Jinja2.
- Các trang nhận dữ liệu từ form HTML, render bằng Jinja2 và chuyển trang sau khi lưu thành công.
- Giữ chức năng, tên trường, kiểu dữ liệu, đường dẫn và giao diện Employee/Department đang chạy của A.
- Employee/Department của B là phần thử nghiệm: thay bằng phần A, nhưng rà soát và chuyển các logic Auth/User đang phụ thuộc vào phần thử nghiệm trước khi bỏ.
- Không chuyển phần A sang frontend gọi API JSON. Không giữ hai bộ Employee/Department cùng xử lý một chức năng.
- Không giữ hai cơ chế đăng nhập song song. Chốt đăng nhập web bằng session cookie, trình bày chi tiết ở mục 5.
- Giữ hai vai trò `admin` và `employee_models.py`. Không dùng thêm `owner` hoặc `manager` trong phạm vi hiện tại.
- Code dễ đọc, tên rõ nghĩa; không viết rút gọn khó hiểu. Theo yêu cầu môn học A đã cung cấp, không thêm `try/except` trong code ứng dụng; dùng kiểm tra điều kiện và kết quả lỗi rõ ràng.

Jinja2 chỉ tạo HTML. Logic kiểm tra mật khẩu, phân quyền và làm việc với database vẫn là Python; không phải chuyển các logic đó thành template.

## 2. Những khác biệt cần xử lý

Đối chiếu với bản B đã fetch tại `origin/main` (commit `97eb757`); nếu B có bản mới hơn, cần kiểm tra lại thay đổi trước khi tích hợp.

| Hạng mục | Bản B đang có | Quyết định tích hợp |
|---|---|---|
| Employee/Department | API JSON và model thử nghiệm riêng | Dùng phần A |
| Login | Nhận JSON, trả access/refresh token | Nhận form, tạo session cookie, redirect |
| Nhận diện đăng nhập | `OAuth2PasswordBearer`, đọc Authorization header | Đọc session, tra tài khoản hiện tại trong DB |
| Giao diện Login/Profile | Chưa có template trong bản đã kiểm tra | B bổ sung Jinja2 |
| Mã nhân viên | ID số + `employee_code` | `Employee.id` là chuỗi tối đa 20 ký tự |
| Tên/ngày vào làm/trạng thái | `full_name`, `hire_date`, `is_active` | `name`, `start_date`, `status` của A |
| Hồ sơ | Thiếu birthday/gender/phone/address | Giữ đầy đủ model A |
| Email/chức vụ/ngày vào làm | Bắt buộc trong model B | Cho phép trống theo model A |
| Vai trò | owner/manager/employee | admin/employee |
| Mật khẩu ban đầu | Hàm tạo user lấy email làm mật khẩu | Không dùng email làm mật khẩu |

Cấu trúc module và việc dùng token của B không tự thân là lỗi kỹ thuật. Vấn đề là khác hợp đồng dữ liệu và luồng web đã thống nhất. Phần API thử nghiệm không phải sản phẩm giao diện hoàn chỉnh theo plan.

## 3. Một cấu trúc thư mục chung

Giữ cấu trúc A đang có, bao gồm Department đã tách. Hoàn thiện theo cấu trúc dưới đây; đây là cấu trúc đích, một số file chưa tồn tại:

```text
hr-management-web/
  main.py
  requirements.txt
  .env.example
  README.md
  PLAN_FASTAPI_MYSQL.md
  app/
    config.py
    database.py
    models/
      department.py
      employee.py
      user.py
    modules/
      department/
        department_router.py
        department_service.py
      employee/
        employee_router.py
        employee_service.py
      auth/
        auth_router.py
        auth_service.py
        dependencies.py
        security.py
    templates/
      base.html
      login.html
      employees/
        list.html
        form.html
        edit.html
        detail.html
      departments/
        list.html
        edit.html
      profile/
        profile.html
    static/
      css/
      js/
  tests/
  seed.py
```

- Chỉ một `Base`, một `engine`, một `SessionLocal`, lấy từ `app/database.py`.
- Chỉ một nơi đọc cấu hình: `app/config.py`; không giữ thêm `app/core/database.py` hoạt động song song.
- Tất cả model ở `app/models/`; không đăng ký hai class cùng ánh xạ bảng employees hoặc departments.
- Router nhận request/form và trả HTML/redirect. Service xử lý nghiệp vụ và dữ liệu. Không viết SQL trong template.
- Không bắt buộc thêm lớp repository. Chuyển phần truy vấn cần dùng của B vào service để tránh duy trì hai cách tổ chức cùng một chức năng.
- Schema Pydantic chỉ giữ nếu có nơi thực sự dùng; không giữ các response schema/token schema đã mất người gọi. Không bắt A chuyển form sang JSON để sử dụng schema của B.
- `main.py` lắp ứng dụng, middleware và router. Chuyển dần logic Employee còn trong main vào module Employee, giữ hành vi đang chạy.
- Không lồng thêm một dự án `hr_management/` có main/database/requirements riêng bên trong repo.

## 4. Hợp đồng database

### Department — giữ model A

| Trường | Kiểu và ràng buộc |
|---|---|
| id | Integer, khóa chính, tự tăng |
| name | String(100), bắt buộc, duy nhất |

### Employee — giữ model A

| Trường | Kiểu và ràng buộc |
|---|---|
| id | String(20), khóa chính; ví dụ NV001 |
| name | String(100), bắt buộc |
| birthday | Date, có thể trống |
| gender | String(20), có thể trống |
| phone | String(20), có thể trống |
| email | String(255), có thể trống, duy nhất khi có giá trị |
| address | String(255), có thể trống |
| position | String(100), có thể trống |
| start_date | Date, có thể trống |
| department_id | Integer, khóa ngoại departments.id, bắt buộc |
| status | String(20), Active hoặc Inactive; mặc định Active |

Giữ quy tắc xử lý dữ liệu của A, bao gồm chuẩn hóa trường tùy chọn rỗng thành `None` khi lưu. Không đổi mã nhân viên thành số. Trạng thái nhân viên `status` khác với cờ khóa tài khoản `User.is_active`.

### User — B điều chỉnh

- `id`: Integer, khóa chính.
- `username`: String(100), bắt buộc, duy nhất.
- `password_hash`: chuỗi hash mật khẩu; thống nhất tên theo plan, sửa các chỗ B đang dùng `hashed_password`.
- `role`: chỉ `admin` hoặc `employee_models.py`.
- `employee_id`: String(20), khóa ngoại employees.id, duy nhất. Cho phép NULL cho tài khoản admin khởi tạo; tài khoản employee phải gắn với nhân viên tồn tại.
- Có thể giữ `is_active` để khóa tài khoản; phải kiểm tra khi đăng nhập và khi truy cập trang được bảo vệ.
- Chưa đưa luồng bắt buộc đổi mật khẩu/refresh token vào bản ghép này; loại bỏ các tham chiếu không còn dùng.
- Để tương thích model A hiện chưa có thuộc tính `user`, không giữ `back_populates="user"` chưa có phía đối ứng. Có thể truy vấn Employee bằng `db.get(Employee, user.employee_id)` khi lấy profile; không bắt buộc thêm relationship.

Sửa tất cả tham số, schema và truy vấn còn giả định employee_id là số. Bảng đã tồn tại trong MySQL phải được cập nhật tương ứng: `create_all()` không tự sửa cột cũ. Chuẩn bị script chuyển đổi có kiểm tra hoặc dùng database thử nghiệm mới; không xóa database/dữ liệu của A. Nếu có user thử nghiệm dùng ID số, phải ánh xạ sang mã nhân viên đúng, không ép kiểu số thành chuỗi rồi coi là đã khớp.

## 5. Chốt đăng nhập web: session cookie

Chọn session cookie cho bản tích hợp này, dùng `SessionMiddleware` của Starlette. B tái sử dụng hàm hash/verify mật khẩu và truy vấn User đang có; thay luồng phát access/refresh token.

SessionMiddleware lưu dữ liệu session trong cookie có chữ ký, không phải kho session trên server. Nội dung cookie có thể đọc được, nên chỉ lưu thông tin tối thiểu như `user_id` và CSRF token; không lưu mật khẩu, password hash hay hồ sơ cá nhân. Khóa ký lấy từ biến môi trường và không commit.

Luồng thống nhất:

1. GET `/login`: hiện form username/password.
2. POST `/login`: nhận `Form`, kiểm tra tài khoản và mật khẩu. Sai thì render lại login với thông báo dễ hiểu; không đưa mật khẩu vào context để hiện lại.
3. Thành công: xóa dữ liệu session cũ, tạo session mới, lưu user_id; chuyển bằng HTTP 303 đến `/employees` nếu admin, `/profile` nếu employee.
4. Mỗi request được bảo vệ: lấy user_id từ session, đọc lại User trong DB để kiểm tra tài khoản còn tồn tại, còn hoạt động và quyền hiện tại. Không lấy role do form gửi lên làm căn cứ.
5. POST `/logout`: kiểm tra CSRF, xóa session và chuyển về `/login`.

Cookie dùng HttpOnly, SameSite=Lax, thời hạn hữu hạn; bật Secure khi chạy HTTPS. Local HTTP có cấu hình phù hợp để cookie vẫn hoạt động. Các form POST phải có CSRF token được kiểm tra phía server, kể cả logout; SameSite không thay thế toàn bộ kiểm tra CSRF.

Logout xóa cookie trên trình duyệt hiện tại; session cookie có chữ ký không tự thu hồi mọi bản sao cookie đã bị lấy cắp. Thu hồi tất cả phiên là chức năng ngoài bản ghép này. Tài khoản bị khóa vẫn phải bị chặn ngay nhờ kiểm tra DB mỗi request.

Không duy trì song song `/auth/login` trả token, OAuth2PasswordBearer và login session cho cùng website. Bỏ các route refresh/token và code thừa khỏi bản ứng dụng tích hợp sau khi kiểm tra không còn người gọi; không tự ý xóa bảng/dữ liệu cũ trong DB.

## 6. Các file B cần chỉnh

| File/chức năng B | Công việc |
|---|---|
| auth_router.py | GET/POST login, POST logout, GET profile; nhận form và trả HTML/redirect |
| auth_service.py | Giữ kiểm tra mật khẩu/tài khoản; trả kết quả và lỗi rõ ràng cho router; bỏ phụ thuộc phát refresh/access token |
| dependencies.py | Đọc session; kiểm tra đăng nhập, User.is_active và role |
| security.py | Giữ hash/verify mật khẩu, hỗ trợ kiểm tra CSRF; bỏ hàm token không còn dùng |
| user_models.py | Chuyển model về app/models/user.py; sửa tên trường, role, employee_id và quan hệ theo mục 4 |
| user_repository.py | Chuyển truy vấn cần thiết vào service theo cấu trúc thống nhất; bỏ file sau khi hết tham chiếu |
| auth_schemas.py | Bỏ schema chỉ phục vụ API đã bỏ; cập nhật kiểu employee_id nếu còn dùng schema |
| refresh_token_* | Không nằm trong luồng session đã chốt; bỏ code/import không còn dùng |
| Employee service thử nghiệm | Tách ra logic tạo tài khoản/phân quyền còn cần dùng trước khi bỏ |
| main.py | Một ứng dụng; cấu hình SessionMiddleware, đăng ký router; bỏ route thử nghiệm trùng |
| login.html và profile/profile.html | B tạo giao diện Jinja2 dùng cùng base.html với các trang A |

Auth service nên trả kết quả nghiệp vụ để router dùng `if` phân biệt thành công/thất bại. Lỗi form thông thường phải hiển thị trên trang; không để người dùng chỉ nhìn thấy JSON hoặc Internal Server Error.

## 7. Quyền truy cập và tạo tài khoản

| Người dùng | Quyền |
|---|---|
| Chưa đăng nhập | Mở login; khi mở trang được bảo vệ thì chuyển về login, không thực hiện thao tác ghi |
| admin | Quản lý Employee/Department và xem hồ sơ nhân viên |
| employee | Chỉ xem profile của chính mình; không truy cập trang quản trị |

- B cung cấp hàm kiểm tra đăng nhập và hàm yêu cầu admin; A gắn vào mọi route Employee/Department, cả GET và POST.
- Profile lấy employee_id từ User đã xác thực, không từ mã tùy ý trong URL/form.
- Employee truy cập trang quản trị nhận 403 với nội dung dễ hiểu. Ẩn nút không thay thế kiểm tra phía server.
- Nếu nhân viên bị chuyển Inactive, tài khoản employee liên kết không được tiếp tục sử dụng trang được bảo vệ; kiểm tra trạng thái nhân viên khi xác thực quyền truy cập của employee.
- B chuẩn bị `seed.py` để tạo tài khoản admin và employee phục vụ demo, liên kết tới mã nhân viên có thật. Chạy lại không tạo trùng hoặc tự đổi mật khẩu tài khoản có sẵn.
- Mật khẩu khởi tạo được nhập khi chạy hoặc lấy từ cấu hình local không commit; lưu hash trong DB. Không dùng email làm mật khẩu.
- Bản ghép hiện tại không tự tạo tài khoản khi A thêm nhân viên. Tạo nhân viên và tạo tài khoản là hai việc riêng; chưa cần trang quản trị tài khoản nâng cao.

## 8. Chia việc và thứ tự ghép

1. A hoàn thiện tách Employee ra module như Department, giữ nguyên tính năng đã kiểm thử.
2. B chỉnh User/Auth theo hợp đồng trong tài liệu này, làm login/profile/logout và seed tài khoản.
3. Ghép vào một cấu trúc và một database config; loại bỏ model/router thử nghiệm trùng. Không ghi đè toàn bộ thư mục A một cách máy móc.
4. B và A gắn kiểm tra quyền, CSRF vào các form/route A, dùng chung base.html và nút logout.
5. Chạy kiểm thử mục 9 trên database thử nghiệm; sau đó kiểm tra dữ liệu hiện có của A với phương án cập nhật không làm mất dữ liệu.
6. Dọn import, file và route không còn dùng; cập nhật requirements, .env.example, README. Commit bản tích hợp sau khi kiểm tra hoàn tất theo mong muốn của A.

Chỉ một requirements.txt, một lệnh chạy từ gốc repo: `python -m uvicorn main:app --reload` với Python của môi trường ảo. Hai máy có database local riêng nhưng cùng cấu trúc và cùng script khởi tạo; không cần cùng mật khẩu MySQL.

## 9. Điều kiện hoàn tất và kiểm tra cùng nhau

- [ ] Cài dependencies và khởi động được trên máy cả A và B theo README.
- [ ] Login sai hiện thông báo trên form; login đúng chuyển đúng trang theo role.
- [ ] Mở trang bảo vệ khi chưa login bị chuyển về login; POST trực tiếp không login không làm đổi dữ liệu.
- [ ] Employee không xem danh sách/quản trị nhân viên, không thêm/sửa phòng ban hoặc nhân viên bằng POST trực tiếp.
- [ ] Profile chỉ hiển thị đúng nhân viên gắn với tài khoản đang login.
- [ ] Logout xong không mở được trang bảo vệ bằng phiên trình duyệt đó.
- [ ] Thiếu/sai CSRF token bị từ chối và không ghi dữ liệu.
- [ ] Khóa tài khoản hoặc chuyển nhân viên employee sang Inactive thì truy cập bị chặn.
- [ ] Department: danh sách/thêm/sửa/chặn tên trùng vẫn hoạt động.
- [ ] Employee: danh sách/thêm/sửa/chi tiết/Inactive vẫn hoạt động.
- [ ] Tìm kiếm giữ tham số `q`; lọc phòng ban, chức vụ, status và kết hợp các bộ lọc vẫn hoạt động.
- [ ] Validation A vẫn còn: trống, trùng mã/email, ngày không hợp lệ, phòng ban không tồn tại; form lỗi giữ dữ liệu đã nhập và không hiện chữ None.
- [ ] Trường tùy chọn trống vẫn lưu được; toàn bộ trường hồ sơ A vẫn hiển thị/chỉnh sửa được.
- [ ] Restart server không mất dữ liệu; seed chạy lại không tạo trùng hoặc đổi mật khẩu đã có.
- [ ] Không còn hai Employee model, hai database config, hai bộ router cùng chức năng hoặc hai cơ chế login.
- [ ] Các trang sản phẩm trả HTML/redirect. JSON phục vụ kỹ thuật như health check nếu có không phải lỗi kiến trúc; bỏ các route demo nghiệp vụ không còn dùng.
- [ ] Không commit .env, mật khẩu, .venv, cache hoặc dữ liệu kiểm thử nhạy cảm.

Sau khi sửa, B gửi danh sách file thay đổi, cách chạy, cách tạo hai tài khoản demo và kết quả kiểm thử. Hai người đối chiếu checklist này trước khi coi là ghép xong. Nếu có vướng mắc, nêu rõ chỗ không tương thích; không tự đổi lại model A, vai trò hoặc luồng Jinja2.
