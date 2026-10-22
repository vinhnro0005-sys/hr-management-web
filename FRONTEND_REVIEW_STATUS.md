# Trạng thái frontend và user/login để nhận xét

Ngày rà soát và đóng gói: 22/10/2026.

## Frontend đã tới đâu?

Frontend đã đủ các màn hình thuộc phạm vi đã chốt để nhận xét thiết kế: đăng nhập; nhân viên (danh sách, tìm/lọc, thêm, sửa, chi tiết, ngừng hoạt động); phòng ban (danh sách, thêm, sửa); hồ sơ cá nhân admin và employee. Có theme sáng/tối, avatar SVG cục bộ, responsive, menu mobile, label/focus, empty state và lỗi biểu mẫu.

Các form nguồn vẫn dùng GET/POST theo FastAPI/Jinja2 hiện có. Không thêm SPA, JSON API hoặc dữ liệu nhân sự trong localStorage. Mã sản phẩm không có dữ liệu mẫu của bản xem tĩnh.

Phần FE còn lại chủ yếu là vòng nhận xét của bạn: màu sắc, cỡ chữ, khoảng cách, mức độ thoáng của bảng/form và bố cục mobile. Nút hiện/ẩn mật khẩu là một cải thiện FE tùy chọn, hiện chưa có; không cần coi đây là điều kiện đăng nhập hoạt động. Không cần bổ sung màn hình của prototype mà backend chưa hỗ trợ.

## User và login: đã có và còn thiếu

| Hạng mục | Hiện có | Còn lại / phạm vi |
|---|---|---|
| Đăng nhập | Form thật username/password, session cookie, kiểm tra mật khẩu hash; lỗi hiển thị trên trang; giữ username, không giữ password | Cần xác nhận tài khoản và kiểm thử trên MySQL hiện tại; lần rà soát này không truy cập database |
| CSRF đăng nhập | GET cấp token, POST kiểm tra token, lỗi cấp token mới | Đã có trong code; không đồng nghĩa các POST khác cũng được bảo vệ |
| Điều hướng theo quyền | Admin tới `/employees`, employee tới `/profile`; dependencies chặn truy cập quản trị | Giữ nguyên; cần kiểm thử lại với tài khoản MySQL thử phù hợp |
| Đăng xuất | FE dùng POST, backend xóa session và về login | Backend chưa kiểm tra CSRF logout; GET logout vẫn xóa session. Bạn đã chọn giữ nguyên, xử lý sau |
| Hồ sơ cá nhân | Đọc hồ sơ từ employee_id của tài khoản; hiển thị thông tin và tài khoản chưa liên kết | Chưa có chức năng tự sửa hồ sơ hoặc upload ảnh, ngoài phạm vi backend hiện tại |
| Cấp tài khoản | Có hàm `AuthService.create_user` và script seed mẫu | Chưa có trang/route quản trị tài khoản. Thêm nhân viên không tự tạo User. Quy trình cấp tài khoản và gắn với nhân viên còn phải chốt nếu muốn quản lý ngay trên web |
| Khóa tài khoản | Có `User.is_active`; Auth kiểm tra tài khoản hoạt động và nhân viên liên kết còn Active | Chưa có màn hình/route khóa hoặc mở khóa tài khoản |
| Mật khẩu | Có hash/verify và ô nhập mật khẩu | Chưa có đổi mật khẩu, quên mật khẩu hoặc đặt lại mật khẩu. Đây là mở rộng cần backend và sự đồng ý riêng |
| Lỗi truy cập 403/404 | Backend trả phản hồi lỗi hiện có | Chưa có trang HTML lỗi chung được nối qua backend. Không dựng trang giả để khẳng định đã tích hợp |
| Tên người dùng trên header | Trang profile có user context; các trang quản trị hiển thị liên kết “Hồ sơ cá nhân” | Nếu muốn hiện tên tài khoản trên mọi trang thì cần backend truyền context; chưa sửa |

Không cần đăng ký tài khoản công khai, OAuth, JWT hoặc “ghi nhớ đăng nhập” riêng để hoàn tất MVP đã chốt. Không tự thêm các chức năng này chỉ để lấp giao diện.

Một điểm dọn code backend đã đọc thấy: `load_employee_and_department` ghi annotation `employee_id: int | None`, trong khi model và giá trị thực tế dùng mã chuỗi. Đây là annotation cần sửa cho nhất quán khi được phép; không coi nó là bằng chứng đăng nhập đang hỏng, và chưa sửa trong lần này.

## Việc backend vẫn hoãn

CSRF cho POST quản trị/logout và xử lý GET logout vẫn giữ nguyên theo lựa chọn “Giữ nguyên backend, xử lý sau” của bạn. Không xin lại quyền hoặc thực hiện các thay đổi đó trong lần đóng gói này. Báo cáo tích hợp trước có phương án cụ thể để dùng khi bạn quyết định xử lý.

Không kết luận rằng MySQL hiện thiếu bảng users: ghi chú ngày trước từng nêu điều đó, nhưng trạng thái database chưa được kiểm tra lại sau hướng dẫn seed. Không chạy seed hoặc thay tài khoản để chuẩn bị gói xem FE.

## Gói ZIP dùng để nhận xét

File: `output/HR_FRONTEND_REVIEW_2026-10-22.zip`.

- Giải nén toàn bộ rồi mở `index.html`; không cần đăng nhập, Python hoặc MySQL.
- Có 18 trang/trạng thái minh họa và một trang danh mục, được render từ đúng template nguồn. Có login lỗi, bộ lọc đã chọn, danh sách rỗng, lỗi nhập liệu, hồ sơ Active/Inactive và profile theo role.
- Mỗi trang preview có nhãn dữ liệu minh họa. Form bị chặn gửi và thông báo rõ chưa đăng nhập/lưu dữ liệu. Không có thành công CRUD giả hoặc tài khoản thật.
- Theme và menu mobile hoạt động; tìm/lọc và thao tác ghi chỉ hoạt động khi chạy project FastAPI. Trong gói tĩnh, chọn trạng thái có sẵn để nhận xét.
- Mã nguồn FE nguyên bản nằm trong `app/templates` và `app/static`; preview nằm riêng. Chỉ thay đường dẫn trên bản HTML render phục vụ xem tĩnh, không đổi hợp đồng trong template nguồn.
- Có 5 ảnh QA trước đó và báo cáo tích hợp. Không kèm `.env`, backend Python, seed, database, `.git`, venv hoặc node_modules.

## Mức kiểm tra

- Trước lần đóng gói: đã kiểm thử Auth/Employee bằng SQLite RAM, 80 tổ hợp responsive và tương tác theo báo cáo ngày 21/10; không trình bày đây là test MySQL.
- Lần đóng gói này: đối chiếu lại code user/login; render toàn bộ preview; xác minh link/asset tương đối và nguồn FE khớp byte với project.
- Kiểm tra gói và bản xem tĩnh qua trình duyệt được ghi trong `PACKAGE_CHECKS.md` bên trong ZIP sau khi thực hiện. Các kiểm tra bản tĩnh không phải kiểm thử chức năng Auth/database.

Frontend sẵn sàng cho vòng nhận xét. Nghiệm thu toàn hệ thống vẫn cần môi trường MySQL thử và xử lý các phần backend khi bạn cho phép.
