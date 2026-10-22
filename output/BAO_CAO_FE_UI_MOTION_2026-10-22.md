# Báo cáo nâng cấp giao diện và animation frontend

Ngày: 22/10/2026
Phạm vi: chỉ `app/templates` và `app/static`. Không sửa backend, database, route, form action, method, tên input hay CSRF field.

## 1. Nội dung gói

| Thư mục / file | Nội dung |
|---|---|
| `app/templates/` | Toàn bộ template Jinja2 sau khi sửa |
| `app/static/` | `css/style.css`, `js/app.js`, `js/theme.js`, avatar SVG |
| `screenshots/` | Ảnh chụp trước/sau ở 1280, 1366, 1440 và 1920 px, Light và Dark |
| `CHANGES.diff` | Toàn bộ thay đổi so với commit gần nhất (`dc2e52e`) |
| `BAO_CAO_FE_UI_MOTION_2026-10-22.md` | Báo cáo này |

Để chạy thật, chép `app/templates` và `app/static` đè vào project rồi chạy FastAPI như bình thường. Gói không có backend, `.env` hay database.

## 2. Sửa lỗi nút "Sửa" bị xuống dòng (P0)

- **Nguyên nhân:**
  - Ở bảng phòng ban, cột thao tác rộng `100px` (đã tính cả padding), nên phần còn lại cho nút chỉ khoảng 64px.
  - Thêm vào đó, `td { overflow-wrap: anywhere }` cho phép trình duyệt bẻ chữ ngay trong nút.
  - Kết quả là nút chỉ rộng 64px, cao 52px, chữ "Sử" nằm trên và "a" nằm dưới. Ảnh: `screenshots/BEFORE-departments-nut-sua-bi-xuong-dong.png`.
- **Cách sửa (sửa đúng nguyên nhân, không thêm `!important`):**
  - `.button` luôn `white-space: nowrap`.
  - Ô thao tác dùng `white-space: nowrap; overflow-wrap: normal`.
  - Cột thao tác bảng phòng ban co theo nội dung. Cột thao tác bảng nhân viên rộng cố định 184px, các cột khác được chia lại.
- **Kết quả:**
  - Mọi nút trong bảng nằm trên một dòng và cao đều 34px.
  - Nút Xem và Sửa giờ cùng một kiểu nút: icon và chữ thẳng hàng, có hover và focus.

## 3. Motion design system

Các token khai báo trong `:root` của `style.css`:

- **Thời lượng:** `--motion-instant` 90ms, `--motion-fast` 140ms, `--motion-base` 220ms, `--motion-slow` 380ms, `--motion-entrance` 460ms.
- **Đường cong (easing):**
  - `--ease-standard`: đường cong chính, dùng cho đa số chuyển động.
  - `--ease-out`: dùng khi phần tử xuất hiện.
  - `--ease-in`: dùng khi phần tử biến mất.
  - `--ease-spring`: hơi nảy, dùng cho icon.
- **Độ trễ giữa các phần tử nối tiếp:** `--stagger` 28ms.
- **Màn đăng nhập:** chuỗi xuất hiện dài nhất khoảng 650ms.
- **Công nghệ:** ưu tiên CSS transition/keyframes, dùng Web Animations API khi cần JS điều khiển, và View Transitions API khi trình duyệt hỗ trợ. Không dùng GSAP.
- **Giảm chuyển động:** khi người dùng bật `prefers-reduced-motion`, toàn bộ animation và chuyển trang được tắt.

## 4. Animation theo từng thành phần

### Chuyển trang
- **Có hỗ trợ (Chrome/Edge mới):** dùng View Transitions API. Nội dung trang cũ mờ đi; trang mới mờ dần vào, trượt nhẹ lên và hơi nhòe lúc đầu. Sidebar và topbar đứng yên.
- **Không hỗ trợ:** dùng hiệu ứng CSS xuất hiện thay thế.
- Việc chuyển trang không bị chậm lại.

### Sidebar
- **Mục đang chọn:** có nền nhạt và một thanh dọc bên trái. Thanh này trượt sang mục mới khi chuyển trang.
- **Hover:** nền trượt vào và icon nhích nhẹ.
- **Khi nhấn và sau khi tới trang mới:** mục được nhấn có phản hồi nhẹ, icon của mục vừa chọn nảy lên một lần.
- **Bố cục:** bỏ ghi chú trang trí ở cuối sidebar. Nhãn nhóm hiển thị "Quản trị" hoặc "Cá nhân".

### Bảng nhân viên và phòng ban
- **Khi tải trang:** các hàng xuất hiện lần lượt. Chỉ 10 hàng đầu có độ trễ, nên danh sách dài không bị chậm.
- **Hover hàng:** nền đổi màu và có viền nhấn bên trái. Dùng `box-shadow` nên không lệch layout.
- **Nút Xem và Sửa:** mắt của nút Xem nhích sang phải, bút chì của nút Sửa nghiêng khi hover.
- **Tìm/Lọc:** bảng mờ đi và nút hiện vòng xoay trong lúc chờ kết quả.
- **Danh sách rỗng:** icon nằm trong khối màu nhạt và có animation xuất hiện.

### Form thêm/sửa nhân viên và phòng ban
- **Xuất hiện:** các nhóm trường và từng trường xuất hiện theo thứ bậc.
- **Focus:** viền có quầng màu, label đổi màu, icon tìm kiếm phóng nhẹ.
- **Lỗi nhập liệu:**
  - Lỗi hiện ngay dưới từng trường, bằng tiếng Việt. Ví dụ: "Vui lòng nhập họ và tên.", "Vui lòng chọn phòng ban.", "Email chưa đúng định dạng…".
  - Con trỏ nhảy tới ô sai đầu tiên. Lỗi tự ẩn khi đã sửa đúng.
  - Lỗi được gắn vào trường qua `aria-describedby`.
- **Lỗi từ server:** khung lỗi trượt vào và rung nhẹ một lần.
- **Nút gửi:** chỉ hiện vòng xoay "Đang gửi…" khi request thật sự đang gửi; nút giữ nguyên độ rộng. Nút được khôi phục khi người dùng bấm quay lại (Back).

### Trang đăng nhập
- **Xuất hiện:** khối giới thiệu, tiêu đề và form xuất hiện theo trình tự. Đường nối vẽ ra, ba thẻ avatar SVG rơi vào chỗ.
- **Theo chuột:** một quầng sáng nhẹ và hình minh họa di chuyển theo chuột. Chỉ dùng transform, không có chuyển động lặp vô tận.
- **Nội dung:**
  - Câu giới thiệu rút gọn, chỉ mô tả chức năng thật.
  - Thông báo lỗi đăng nhập chuyển vào trong thẻ đăng nhập.
  - Bỏ footer khỏi trang này.

### Thông báo và hộp thoại
- **Toast thành công:** trượt vào, có dấu tích vẽ bằng SVG, tự ẩn sau khoảng 4,5 giây (dừng đếm khi rê chuột vào) và có nút đóng.
  - Backend không gửi thông báo thành công, nên toast được làm hoàn toàn ở frontend. Nó chỉ hiện khi server đã chuyển sang một trang khác với địa chỉ của form, vì khi có lỗi server trả về đúng địa chỉ đó.
  - Áp dụng cho: thêm nhân viên, sửa hồ sơ, ngừng hoạt động nhân viên, thêm phòng ban, sửa phòng ban.
- **Tô sáng hàng:** sau khi thêm nhân viên hoặc phòng ban, hàng vừa tạo được tô sáng trong danh sách.
- **Hộp xác nhận "Ngừng hoạt động":** `window.confirm` được thay bằng hộp thoại `<dialog>`.
  - Mở và đóng đều có animation.
  - Nút "Hủy" được focus sẵn cho an toàn.
  - Đóng được bằng Esc hoặc bấm ra ngoài.
- **Phản hồi khi nhấn:** mọi nút có phản hồi khi nhấn.

### Light/Dark Mode
- **Chuyển theme:** giữ nút chuyển theme cũ. Đổi theme có crossfade; icon mặt trời/mặt trăng xoay và đổi qua lại.
- **Không lỗi khi chuyển:** không nháy sai theme khi tải trang, không mất focus, không tải lại trang.

## 5. Tinh chỉnh giao diện

- **Typography:** chữ phụ tăng từ 11–12px lên 12–13,5px (header bảng, mã nhân viên, badge trạng thái, gợi ý dưới ô nhập, footer).
- **Khoảng cách:**
  - Topbar giảm từ 80px xuống 64px.
  - Padding trang, panel và form được thu gọn.
  - Bộ lọc nằm trên một hàng cùng nút Tìm/Lọc.
- **Nút:** một chiều cao chuẩn 42px, nút nhỏ 34px. Bo góc thống nhất, focus ring rõ ràng. Thêm kiểu nút `button-ghost`.
- **Form:** dải hành động cuối form có nền riêng. Mỗi tiêu đề nhóm trường (legend) có đường kẻ phân cách.
- **Hồ sơ nhân viên:**
  - Phần đầu có nền chuyển màu nhẹ.
  - Tiêu đề từng mục rõ hơn.
  - Giá trị đậm hơn nhãn.
- **Hồ sơ cá nhân:** khối "Tài khoản đăng nhập" có icon và dòng vai trò. Cảnh báo tài khoản chưa liên kết hồ sơ hiển thị bằng màu amber.
- **Footer:** bỏ tagline "Thông tin rõ ràng · Quản lý thuận tiện".
- **Phong cách:** giữ teal/mint ở chế độ sáng và navy ở chế độ tối. Không thêm logo, không thêm chữ kiểu "Premium" hay "AI".

## 6. File đã thay đổi

**Static:**
- `app/static/css/style.css`: motion tokens, View Transitions, sửa cột thao tác, toàn bộ animation và tinh chỉnh giao diện.
- `app/static/js/app.js`: chuyển theme, thanh đánh dấu ở sidebar, kiểm tra lỗi form, trạng thái đang gửi, hộp xác nhận, toast, tô sáng hàng, hiệu ứng theo chuột ở trang đăng nhập.
- `app/static/js/theme.js`: đánh dấu khi đang có chuyển trang, chặn thông báo lỗi "Transition was skipped" trong console.

**Template:**
- `base.html`: thêm quầng sáng cho trang đăng nhập, đổi vị trí thông báo lỗi trên trang đăng nhập, bỏ footer ở trang đăng nhập.
- `components/`:
  - `sidebar.html`: thêm thanh đánh dấu mục đang chọn, bỏ ghi chú trang trí.
  - `ui.html`: icon mặt trời/mặt trăng, icon `eye`, icon `key`, thêm class `icon-<tên>` cho từng icon.
- `employees/`:
  - `list.html`: đổi nút Xem/Sửa, thêm `data-row-key` cho hàng, trạng thái chờ khi lọc.
  - `form.html`, `edit.html`, `detail.html`: thêm thuộc tính `data-success` để hiện toast; `detail.html` thêm tiêu đề cho hộp xác nhận.
- `departments/list.html`, `departments/edit.html`: `data-row-key`, `row-actions`, `data-success`.
- `login.html`: viết lại câu giới thiệu, đặt khung lỗi trong thẻ đăng nhập.
- `profile/profile.html`: bố cục mới cho khối tài khoản.

Các thuộc tính `data-*` mới chỉ dùng cho JavaScript. Chúng không được gửi lên server và không đổi dữ liệu form.

## 7. Điều chỉnh so với yêu cầu ban đầu

- **Nút Xóa:** project không có nút Xóa trong bảng, chỉ có "Ngừng hoạt động" ở trang chi tiết. Tôi không thêm nút Xóa, vì như vậy là thêm chức năng mới.
- **Toast:** làm hoàn toàn ở frontend, không sửa backend để thêm thông báo thành công.
- **Nút hiện/ẩn mật khẩu:** chưa thêm, vì ngoài phạm vi animation.
- **Nguồn tham khảo:**
  - Đọc được detail.design và repo Motion2Code.
  - Không truy cập được motionin.design và navbar.gallery (lỗi DNS), nên không nghiên cứu hai nguồn này.

## 8. Kiểm thử đã làm và việc còn lại

Lần đóng gói này không chạy thêm test nào. Kết quả dưới đây là của lần làm trước.

- **Cách chạy:** app thật với SQLite trong bộ nhớ, không dùng MySQL.
- **Đã kiểm tra trên Chrome:**
  - 7 trang × 4 kích thước × 2 theme: không cuộn ngang, không nút nào xuống dòng, không lỗi JavaScript.
  - Chuyển trang bằng View Transitions có chạy.
  - Đổi theme giữ được focus.
  - Khi bật giảm chuyển động, không còn animation nào chạy.
- **Luồng đã chạy thật:** thêm nhân viên, thêm phòng ban, ngừng hoạt động qua hộp xác nhận; lỗi form hiện đúng chỗ.
- **Test sẵn có:** cả 2 file pass khi chạy riêng từng file.
- **Chưa kiểm chứng:**
  - Chưa xem lại giao diện mobile bằng mắt. Các rule responsive cũ vẫn giữ nguyên.
  - Chưa kiểm thử trên MySQL thật.
  - Trình duyệt nhúng trong Claude tự bỏ qua hiệu ứng chuyển trang, nên phần này chỉ được xác nhận trên Chrome.
- **Chưa commit git.**
