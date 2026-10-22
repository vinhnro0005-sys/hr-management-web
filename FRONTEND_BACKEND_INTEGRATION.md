# Báo cáo tích hợp frontend vào FastAPI + Jinja2

Ngày: 21/10/2026. Dự án đích: `hr-management-web`.

Đã triển khai giao diện trên các route nghiệp vụ hiện có. CSS, JavaScript và avatar đã được ứng dụng thật phục vụ qua `/static`. Đã kiểm thử với FastAPI và SQLite trong RAM, chưa kiểm thử với MySQL của người dùng. Chưa nghiệm thu toàn bộ hệ thống: các form quản trị và logout còn thiếu kiểm tra CSRF phía backend, được ghi rõ ở mục 7 và chưa sửa.

## 1. Căn cứ khảo sát

- Đã đọc `PLAN_FASTAPI_MYSQL.md`, `PROJECT_PROGRESS.md`, `HANDOFF_B_INTEGRATION.md`, README, skill `.agents/skills/hr-project-tutor/SKILL.md` và đối chiếu với code.
- Đã khảo sát `main.py`, router Auth/Employee/Department, dependencies, security, service, repository, schema, model và tám template gốc.
- Tham khảo `hr-ui-mockups/v12-zenith-executive/index.html`, `style.css`, `app.js`, `V13_CHANGELOG.md`, cơ chế theme, danh bạ, hồ sơ và cấu trúc kiểm thử `test_v13.mjs`.
- Tài liệu cũ có mô tả JWT/API, cấu trúc khác và cả tên role lỗi `employee_models.py`. Code hiện tại quyết định hợp đồng: session cookie, role `admin`/`employee`, form GET/POST và module model/schema/repository/service/router.
- Các tuyên bố PASS trong changelog của prototype không được dùng làm kết quả kiểm thử lần này. Không chạy `test_v13.mjs` vì nó kiểm thử dữ liệu và chức năng mô phỏng của prototype.
- Không mở hoặc in nội dung `.env`. Không kết nối, seed, migrate hay sửa dữ liệu MySQL. Không commit, push, pull hoặc merge.
- Repo đã có nhiều thay đổi staged/unstaged trước khi bắt đầu. Đã giữ nguyên chúng; so sánh hash lúc bắt đầu xác nhận file ngoài frontend do lần này sửa chỉ là `main.py`.

## 2. Bản đồ chức năng và hợp đồng tích hợp

| Chức năng | Backend thực tế hỗ trợ | Route/phương thức | Template/context/form cần giữ | Cách xử lý giao diện |
|---|---|---|---|---|
| Trang mặc định | Redirect theo đăng nhập và role | `GET /` | Admin → `/employees`; employee → `/profile`; chưa đăng nhập → `/login` | Brand dẫn về `/`, không thêm dashboard |
| Đăng nhập | Session cookie, xác thực tài khoản, kiểm tra CSRF | `GET/POST /login` | `login.html`; `csrf_token`, `error`, `username`; POST `username`, `password`, `csrf_token` | Form thật; giữ username và thông báo lỗi, không hiện lại mật khẩu |
| Đăng xuất | Xóa session, redirect login; hiện chưa kiểm tra CSRF | `POST /logout`, backend còn có `GET /logout` | Không có template kết quả; token có trong session | Giao diện chỉ dùng POST, có hidden token; không coi hidden field là bảo vệ server |
| Danh sách/tìm/lọc nhân viên | Tìm mã/tên, lọc kết hợp phòng ban/chức vụ/trạng thái | `GET /employees` | `employees/list.html`; `employees` là các cặp `(Employee, department_name)`; `q`, `departments`, `positions`, `selected_department`, `selected_position`, `selected_status`; query `q`, `department_id`, `position`, `status` | Giữ lựa chọn; đếm kết quả từ context hiện có; empty state; bảng cuộn ngang |
| Thêm nhân viên | Tạo hồ sơ Active, kiểm tra schema/trùng mã/email/phòng ban | `GET/POST /employees/create` | `employees/form.html`; `departments`, `form_data`, `error`; POST `id`, `name`, `department_id`, `position`, `phone`, `email`, `address`, `gender`, `birthday`, `start_date` | Trang form; giữ dữ liệu lỗi; không thêm trường tài khoản hoặc ảnh |
| Chi tiết nhân viên | Lấy hồ sơ và phòng ban | `GET /employees/{employee_id}` | `employees/detail.html`; `employee`, `department` | Đầy đủ trường hồ sơ, avatar cục bộ, trạng thái dịch nhãn |
| Sửa nhân viên | Cập nhật hồ sơ, không đổi mã và không đổi trạng thái qua form này | `GET/POST /employees/{employee_id}/edit` | `employees/edit.html`; `employee`, `departments`, `form_data`, `error`; các trường tạo trừ `id` | Mã chỉ đọc, không thêm input `status`; dùng chung phần trường với form tạo |
| Ngừng hoạt động | Chuyển sang `Inactive`, gọi lại không đổi thêm dữ liệu | `POST /employees/{employee_id}/deactivate` | Redirect về chi tiết | Xác nhận bằng hộp thoại native; chỉ hiện nút khi Active; không tạo xóa hoặc kích hoạt lại |
| Danh sách/thêm phòng ban | Danh sách, tạo và chặn tên trùng | `GET /departments`, `POST /departments/create` | `departments/list.html`; `departments`, `entered_name`, `error`; POST `name` | Bảng và form thêm cùng trang; giữ tên khi lỗi; không dựng số nhân viên/ngân sách giả |
| Sửa phòng ban | Đổi tên, chặn tên trùng | `GET/POST /departments/{department_id}/edit` | `departments/edit.html`; `department`, `entered_name`, `error`; POST `name` | Form thật; không thêm xóa |
| Hồ sơ cá nhân | Lấy nhân viên liên kết từ tài khoản đang xác thực | `GET /profile` | `profile/profile.html`; `user`, `employee`, `department`, `csrf_token` | Chỉ xem; trường hợp tài khoản không gắn hồ sơ được hiển thị rõ |
| Phân quyền | `require_admin` cho toàn bộ Employee/Department, `get_current_user` cho profile | Dependencies phía server | Role lấy từ User, không từ form | Sidebar quản trị chỉ hiện trên route được bảo vệ dành cho admin hoặc khi context user là admin; profile employee chỉ có mục hồ sơ |

Giữ nguyên giá trị `Active`, `Inactive`, `admin`, `employee`, `Nam`, `Nữ`, `Khác`. Chỉ đổi nhãn hiển thị. Không query database trong Jinja2. Các trang quản trị chưa được truyền `user`: header dùng liên kết “Hồ sơ cá nhân”, không đoán tên người đăng nhập.

CSRF field dùng token context hiện có, hoặc `request.session.get('csrf_token', '')` trên trang quản trị. Không tạo token trong template. Thêm field này không tự bổ sung kiểm tra phía backend.

## 3. Các màn hình giữ lại và loại bỏ

Giữ: đăng nhập, danh sách/tìm/lọc nhân viên, tạo/sửa/chi tiết/ngừng hoạt động, danh sách/thêm/sửa phòng ban và hồ sơ cá nhân.

Không đưa sang ứng dụng: Dashboard, Attendance, Leaves, Recruitment, Onboarding, Payroll/ESOP, AI Insights, Settings/RBAC mô phỏng, Calendar, Notifications, export CSV, upload ảnh, đổi mật khẩu, quản trị tài khoản, đánh giá/9-box, số liệu lương và thống kê giả. Không có link, menu, nút hoặc toast giả dẫn tới các chức năng này. Prototype nguồn vẫn được giữ nguyên.

## 4. Cấu trúc và danh sách file thay đổi

Tám template có sẵn đã sửa, giữ nguyên tên để router tiếp tục render đúng. Bảy template mới dùng lại phần bố cục/hiển thị; bốn asset mới phục vụ cục bộ:

```text
app/
  templates/
    base.html                         [mới]
    components/
      sidebar.html                    [mới]
      header.html                     [mới]
      messages.html                   [mới]
      ui.html                         [mới: macro icon/avatar/status/CSRF]
    login.html                        [sửa]
    employees/
      list.html                       [sửa]
      form.html                       [sửa]
      edit.html                       [sửa]
      detail.html                     [sửa]
      fields.html                     [mới: trường dùng chung thêm/sửa]
      info.html                       [mới: hồ sơ dùng chung detail/profile]
    departments/
      list.html                       [sửa]
      edit.html                       [sửa]
    profile/
      profile.html                    [sửa]
  static/
    css/style.css                     [mới]
    js/theme.js                       [mới]
    js/app.js                         [mới]
    images/avatar-default.svg         [mới]
main.py                               [chỉ thêm mount static cuối file]
FRONTEND_BACKEND_INTEGRATION.md         [báo cáo này]
output/playwright/hr-*.png              [5 ảnh minh chứng thử nghiệm]
```

Không sửa Python Auth, router nghiệp vụ, service, repository, schema, model, cấu hình, requirements hoặc database. Không sửa tài liệu tiến độ/handoff có sẵn. Không thêm dependency ứng dụng. Playwright CLI chỉ dùng ở công cụ kiểm thử ngoài project.

## 5. Những thay đổi giao diện

- Giữ tinh thần teal/mint, dark navy và amber của mẫu. Dùng tên “Hệ thống Quản lý Nhân sự”, không dùng Zenith, số phiên bản hay logo mới.
- Sidebar gọn với ba mục thật cho admin; employee chỉ có hồ sơ. Menu mobile có backdrop, focus trap, Escape và trả focus về nút mở. Khi JavaScript không chạy, điều hướng vẫn nằm trong trang để dùng được.
- Tách rõ tiêu đề, mô tả, vùng tìm/lọc, dữ liệu và thao tác. Dùng bảng với tiêu đề cột, caption, empty state và vùng cuộn có thể focus bằng bàn phím. Nút xem/sửa vẫn nằm trong bảng trên mobile.
- Form dùng label, required, maxlength và input date/tel/email gốc của trình duyệt. Lỗi do backend cung cấp hiển thị ở vùng `role="alert"`; dữ liệu tiếp tục lấy từ `form_data`/`entered_name`.
- Chỉ một avatar silhouette SVG mặc định cục bộ vì model không có trường ảnh. Avatar thống nhất ở bảng và hồ sơ; không gọi Unsplash, font CDN hoặc dịch vụ ảnh ngoài. `alt=""` vì tên đã được hiển thị cạnh avatar.
- `theme.js` đọc theme trước stylesheet để hạn chế nháy sai màu. `app.js` chuyển Light/Dark; chỉ lưu lựa chọn `hr_theme` trong localStorage. Khi storage bị chặn, lựa chọn theme vẫn hoạt động trong trang; không lưu dữ liệu nhân sự hoặc thông tin đăng nhập.
- Chuyển động 180–220ms cho hover/focus/sidebar và xuất hiện trang. `prefers-reduced-motion` tắt transition/animation. Không skeleton, delay giả, SPA router hay fetch CRUD.
- Form POST có trạng thái đang gửi, chặn gửi lặp và phục hồi nút cùng icon khi quay lại từ back/forward cache. Thành công chỉ thể hiện bằng HTML/redirect thật từ backend.
- Jinja vẫn autoescape; không dùng `|safe`, không ghép SVG từ tên người dùng.

## 6. Thay đổi backend đã được cho phép

Thông báo Python đổi từ không dấu sang có dấu: **không có**. Giữ nguyên code thông báo trong lần này, bao gồm các thông báo chưa có dấu. Các nhãn/error heading mới ở frontend dùng tiếng Việt có dấu.

Thay đổi backend ngoài thông báo duy nhất là mount static trong `main.py`. Sau khi được thông báo thiếu mount, người dùng chỉ dẫn trong chat ngày 21/10/2026: “nếu sửa main py thì viết xuống cuối file và đánh dấu sao cho nhìn phát biết chỗ đó là sửa”. Đã thực hiện phần phục vụ asset theo chỉ dẫn đó, đặt đúng cuối file và kẹp giữa hai comment dễ tìm:

```diff
 if __name__ == "__main__":
     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
+
+
+# ================= BẮT ĐẦU THAY ĐỔI FRONTEND (21/10/2026) =================
+# Phục vụ CSS, JavaScript và avatar cục bộ cho các trang Jinja2.
+# Đặt cuối file theo yêu cầu của người dùng.
+from fastapi.staticfiles import StaticFiles
+
+app.mount("/static", StaticFiles(directory="app/static"), name="static")
+# ================= KẾT THÚC THAY ĐỔI FRONTEND ============================
```

Lý do: template cần tải CSS, JS và avatar từ ứng dụng. Ảnh hưởng: thêm route phục vụ file dưới `app/static`, không thay route nghiệp vụ/session/redirect. Chạy từ gốc repo như Jinja hiện có. Lệnh `uvicorn main:app` cũng là target được nhánh `python main.py` sử dụng; mount được đăng ký khi module `main` được import.

Đã kiểm tra trực tiếp ứng dụng gốc với TestClient: bốn URL CSS/JS/SVG trả 200. Đã khởi động ứng dụng gốc bằng Uvicorn trên SQLite RAM và kiểm tra trình duyệt. Bản preview dùng wrapper static chỉ xuất hiện trước khi được phép sửa main; các kết quả cuối đã được chạy lại trên app thật, không dùng wrapper.

## 7. Lỗi backend và đề xuất hoãn theo lựa chọn của người dùng

### Thiếu kiểm tra CSRF cho quản trị và logout — CHƯA SỬA

`app/modules/auth/security.py` đã có hàm so sánh token; `auth_router.py` mới dùng nó ở POST login. Các router Employee/Department và POST logout chưa xác minh token. GET logout còn thay đổi session. Đã tái hiện bằng POST tạo phòng ban không có token trên SQLite RAM: backend vẫn trả 303. Đây là lỗi còn tồn tại, không phải một kiểm tra bảo vệ đạt PASS.

Frontend đã gửi token từ session trên các POST, nhưng hidden field không sửa được lỗi này. Cần duyệt riêng thay đổi Python sau:

1. Trong `app/modules/auth/security.py`, bổ sung dependency đọc token từ form và kiểm tra token session cho POST. Phương án cụ thể:

   ```python
   from fastapi import HTTPException, Request

   async def require_valid_csrf(request: Request):
       if request.method != "POST":
           return
       form = await request.form()
       if not verify_csrf_token(
           request.session.get("csrf_token"), form.get("csrf_token")
       ):
           raise HTTPException(
               status_code=403,
               detail="Phiên làm việc không hợp lệ. Vui lòng tải lại trang.",
           )
   ```

2. Trong `employee_router.py` và `department_router.py`, import dependency cùng `Depends`, rồi đổi khởi tạo router sang `APIRouter(dependencies=[Depends(require_valid_csrf)])`. Dùng `await request.form()` để giữ hợp đồng form schema hiện tại, không thêm context hoặc JSON API. Quyền admin đang gắn trong main vẫn giữ.
3. Trong `auth_router.py`, gắn `Depends(require_valid_csrf)` vào POST logout. GET logout chỉ redirect, không xóa session, hoặc bỏ route GET; cần chốt trong lần sửa được phép. Login giữ cách tạo/refresh/kiểm tra token hiện có.

Ảnh hưởng dự kiến: POST quản trị/logout thiếu hoặc sai token bị 403 và không ghi dữ liệu; token đúng giữ kết quả/redirect hiện có. GET quản trị không cần token; GET logout không còn thay đổi phiên. Không cần sửa database hoặc dependencies.

Cách kiểm tra sau khi được phép: token đúng/sai/thiếu cho từng POST create/edit/deactivate/department/logout; so sánh database trước/sau yêu cầu bị chặn; kiểm tra role employee/chưa login vẫn bị chặn; login và validation vẫn giữ dữ liệu nhập; GET logout không kết thúc phiên.

**Người dùng chọn “Giữ nguyên backend, xử lý sau” ngày 21/10/2026.** Không triển khai phương án CSRF và không sửa thêm backend. Phương án trên chỉ được lưu để tham khảo khi người dùng yêu cầu xử lý sau. Đoạn mount static đã được thêm ở cuối `main.py` theo chỉ dẫn trước đó vẫn được giữ.

### Môi trường MySQL và các giới hạn khác

- Theo tài liệu tiến độ, MySQL trước đó chưa có bảng users/tài khoản. Lần này không truy cập MySQL để xác minh lại hoặc tự khởi tạo. Cần môi trường/tài khoản thử phù hợp trước kiểm thử MySQL.
- Lỗi 403/404 và bộ lọc không hợp lệ vẫn trả kiểu phản hồi backend hiện có, có thể là JSON. Không có HTML error handler mới vì cần thay backend.
- Các thông báo Python không dấu hiện có chưa được sửa trong lần này.
- Kiểm tra tự động không thay thế đánh giá đầy đủ với screen reader hay thử trên thiết bị vật lý. Đã kiểm tra focus/label/semantic cơ bản và trình duyệt desktop emulation.

## 8. Kiểm thử đã thực hiện

### Đọc code

Đã đối chiếu route, methods, fields, context, redirects, query filters, model không có ảnh, auth dependencies và vị trí kiểm tra CSRF. Không suy luận chức năng từ prototype hay checklist cũ.

### Cú pháp và render

| Kiểm tra | Kết quả thực tế |
|---|---|
| `node --check app/static/js/app.js` và `node --check app/static/js/theme.js` | PASS |
| Parse toàn bộ 15 template Jinja | PASS |
| Render 7 trang quản trị/hồ sơ qua FastAPI TestClient | PASS |
| Danh sách phòng ban rỗng được render riêng với context thử | PASS |
| Autoescape tên chứa thẻ script; không dùng safe | PASS |
| `git diff --check` | PASS |

### Backend + database thử trong RAM

Đã chạy `.venv/Scripts/python.exe tests/test_employee_auth_refactor.py`: toàn bộ 12 bước Auth hiện có và các kiểm tra Employee/refactor PASS. Các test chỉ dùng SQLite RAM, không sửa các file test có sẵn.

Harness bổ sung ở thư mục tạm thực hiện 30 kiểm tra chức năng/render/asset và một phép tái hiện lỗ hổng CSRF. Nội dung đã kiểm tra:

- Login thiếu token bị từ chối; admin/employee redirect đúng; logout POST và yêu cầu sau logout về login.
- Employee không thấy liên kết quản trị ở profile; GET Employee/Department và POST quản trị bị 403 với role employee.
- Trang list/create/detail/edit/department/profile trả HTML 200; bốn static asset trả 200 trực tiếp từ ứng dụng.
- Kết hợp `q`, `department_id`, `position`, `status` trả đúng hồ sơ và giữ các lựa chọn.
- Empty state khi tìm không có kết quả.
- Employee create/edit/deactivate, mã trùng, email sai, tùy chọn email trống, ngày sinh tương lai; form lỗi trả 400, có alert và giữ dữ liệu, kể cả phòng ban.
- Department create/edit, trùng tên, quá giới hạn; giữ `entered_name` khi lỗi.
- Không có token ở form quản trị vẫn ghi được trong database thử: **lỗi đã xác nhận, chưa sửa**, không báo PASS bảo vệ CSRF.

Có cảnh báo deprecation từ Starlette TestClient về httpx; test vẫn chạy thành công. Không thay dependency để xử lý cảnh báo này ngoài phạm vi frontend.

### Trình duyệt Chromium qua Playwright CLI

Sau khi mount được thêm vào main, server thử chạy **app gốc** với SessionLocal đã thay bằng SQLite RAM trong tiến trình thử; không dùng MySQL và không dùng wrapper để phục vụ static.

| Kiểm tra | Kết quả |
|---|---|
| 7 trang × 5 độ rộng 360/390/768/1024/1440 × 2 theme | PASS, 70 tổ hợp; scrollWidth không vượt viewport |
| Login × 5 độ rộng × 2 theme | PASS, 10 tổ hợp; có một h1 hiển thị |
| Asset/ảnh trên ma trận 7 trang | PASS, không ảnh hỏng, không HTTP 4xx/5xx, không request ra dịch vụ ngoài |
| Lỗi JavaScript trên ma trận | PASS, không có pageerror |
| Chuyển theme, localStorage và reload | PASS |
| Sidebar mobile mở, focus ban đầu, 14 lần Tab, Escape trả focus | PASS |
| Cuộn bảng mobile và bấm liên kết sửa hồ sơ | PASS |
| GET tìm/lọc và xóa bộ lọc bằng điều hướng thông thường | PASS |
| Hộp thoại ngừng hoạt động và hủy | PASS, nút vẫn dùng được sau khi hủy |
| Reduced motion | PASS, animation-name none và transition-duration 0s |
| Submit listener: disabled/busy, chặn event gửi lặp, phục hồi cả icon khi pageshow | PASS, kiểm tra DOM có chặn điều hướng cho bước này |
| Form thêm phòng ban gửi POST bình thường qua trình duyệt | PASS, tạo đúng một bản ghi trong SQLite RAM |
| Login/logout thực tế qua trình duyệt | PASS |

Không báo đã kiểm thử MySQL, dữ liệu thật, restart persistence, thiết bị vật lý, account lock hoặc mọi trường hợp CSRF. Quyền server hiện có được giữ, nhưng phần thiếu CSRF vẫn là điều kiện chưa đạt nghiệm thu.

### Ảnh minh chứng

Tất cả ảnh dùng dữ liệu thử ở SQLite RAM. Tên và số lượng trong ảnh không phải dữ liệu sản phẩm hoặc mock data được đưa vào template. Đã xem trực tiếp ảnh desktop light/dark và mobile để kiểm tra bố cục. Khi lưu ảnh cuối, kết thúc animation/transition để ảnh không chụp giữa trạng thái chuyển màu.

- `output/playwright/hr-employees-light-1440.png`
- `output/playwright/hr-employees-dark-1440.png`
- `output/playwright/hr-employees-dark-390.png`
- `output/playwright/hr-detail-dark-360.png`
- `output/playwright/hr-login-light-1440.png`

## 9. Cách kiểm tra lại

Từ gốc project, chạy các lệnh sẵn có, không seed MySQL:

```powershell
node --check app/static/js/app.js
node --check app/static/js/theme.js
.\.venv\Scripts\python.exe tests/test_employee_auth_refactor.py
```

Mẫu kiểm tra độc lập bổ sung (Python chạy trong tiến trình mới; tái sử dụng bộ test để gắn SQLite RAM trước khi import app):

```python
import sys
sys.path.insert(0, "tests")
from test_auth_integration import test_auth_full_flow
test_auth_full_flow()

from fastapi.testclient import TestClient
from main import app
client = TestClient(app, follow_redirects=False)
for path in (
    "/static/css/style.css", "/static/js/theme.js",
    "/static/js/app.js", "/static/images/avatar-default.svg",
):
    assert client.get(path).status_code == 200, path
```

Mẫu kiểm tra UI với Playwright CLI khi đã có server thử và phiên đăng nhập admin (lưu đoạn JS vào file tạm, dùng `playwright-cli run-code --filename <file>`; không dùng server dữ liệu thật cho các thao tác ghi):

```javascript
async page => {
  await page.setViewportSize({ width: 390, height: 844 });
  const open = page.getByRole('button', { name: 'Mở điều hướng', exact: true });
  await open.click();
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press('Tab');
    const contained = await page.evaluate(() =>
      document.querySelector('.sidebar').contains(document.activeElement));
    if (!contained) throw new Error('Focus escaped sidebar');
  }
  await page.keyboard.press('Escape');
  if (!await open.evaluate(el => el === document.activeElement))
    throw new Error('Focus was not restored');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const disabledMotion = await page.evaluate(() =>
    getComputedStyle(document.querySelector('main')).animationName === 'none');
  if (!disabledMotion) throw new Error('Reduced motion failed');
  return 'PASS: mobile keyboard navigation and reduced motion';
}
```

Frontend đã được chuyển và nối form/asset trên môi trường thử. Phần CSRF được hoãn theo lựa chọn của người dùng; cần được cho phép lại trước khi triển khai. Kiểm thử trên môi trường MySQL thử phù hợp cũng chưa thực hiện.
