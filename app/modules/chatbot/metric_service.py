import os
from dotenv import load_dotenv
import json
from google import genai
from app.core.security_sql import validate_select_only
from app.modules.chatbot.metric_repository import execute_analytics_query

load_dotenv()
_ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

VIEW_SCHEMA = """
Bảng ảo trong MySQL: v_hr_analytics (
    id VARCHAR(20), -- Mã nhân viên (ví dụ 'NV001')
    name VARCHAR(100), -- Họ và tên (ví dụ 'Nguyễn Văn A')
    gender VARCHAR(20), -- Giới tính ('Nam', 'Nữ')
    birthday DATE, -- Ngày sinh
    phone VARCHAR(20), -- Số điện thoại
    email VARCHAR(255), -- Email
    address VARCHAR(255), -- Địa chỉ
    position VARCHAR(100), -- Chức vụ (ví dụ 'Lập trình viên', 'Trưởng phòng')
    department VARCHAR(100), -- Tên phòng ban (trong DB luôn có chữ 'Phòng ...', ví dụ 'Phòng Công nghệ thông tin')
    start_date DATE, -- Ngày vào làm
    status VARCHAR(20) -- Trạng thái: 'Active' (Đang làm), 'Inactive' (Đã nghỉ)
)

Quy tắc sinh SQL bắt buộc:
1. Chuẩn CSDL là MySQL: Tuyệt đối KHÔNG dùng tiền tố N'...' của SQL Server, chỉ dùng chuỗi bình thường '...'.
2. Khi lọc theo phòng ban (department), chức vụ (position), họ tên (name):
   - LUÔN LUÔN dùng toán tử `LIKE '%...%'` thay vì so sánh bằng '=' để tránh bị lệch tiền tố 'Phòng' hoặc lệch chữ hoa/thường.
   - Viết tắt phòng ban thông dụng: 'CNTT' hoặc 'IT' -> đổi thành: `department LIKE '%Công nghệ thông tin%'`. 'HR' hoặc 'Nhân sự' -> `department LIKE '%Nhân sự%'`.
   - Ví dụ: hỏi 'phòng công nghệ thông tin' -> điều kiện là: `department LIKE '%Công nghệ thông tin%'`.
3. Mặc định chỉ đếm/lấy nhân viên đang làm việc: `status = 'Active'` (trừ khi người dùng hỏi rõ nhân viên đã nghỉ).
4. Nếu là TABLE, bắt buộc thêm LIMIT 50 vào SQL.
"""

def handle_metric_inquiry(question: str) -> dict:
    # 1. Ghép schema View yêu cầu Gemini sinh JSON
    prompt = f"""
    Bạn là chuyên viên truy vấn dữ liệu HRM. Dựa vào schema sau:
    {VIEW_SCHEMA}

    Hãy chuyển câu hỏi thành JSON:
    Câu hỏi: "{question}"

    Format JSON bắt buộc:
    {{
      "widget_type": "STAT_CARD" (khi hỏi đếm/tổng) hoặc "TABLE" (khi hỏi danh sách/liệt kê),
      "sql": "SELECT ... FROM v_hr_analytics ...",
      "response_template": "Câu phản hồi có placeholder {{result}} hoặc {{count}}"
    }}
    Lưu ý: Nếu là TABLE, bắt buộc thêm LIMIT 50 vào SQL.
    """
    resp = _ai_client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    raw_text = resp.text.strip()
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    llm_output = json.loads(raw_text)
    sql_query = llm_output["sql"].strip()

    # 2. Chạy qua hàm security kiểm tra
    validate_select_only(sql_query)

    # 3. Lấy dữ liệu qua Repo Nhánh B
    rows = execute_analytics_query(sql_query)

    # 4. Fill template nội bộ (Dữ liệu DB không gửi lại LLM)
    widget_type = llm_output.get("widget_type", "STAT_CARD")
    template = llm_output.get("response_template", "{result}")

    if widget_type == "STAT_CARD":
        val = list(rows[0].values())[0] if rows and list(rows[0].values()) else 0
        if val is None:
            val = 0
        msg = template.replace("{result}", str(val)).replace("{count}", str(val))
        return {
            "type": "STAT_CARD",
            "message": msg,
            "data": {"value": val}
        }
    else:
        count = len(rows)
        if count > 0:
            msg = template.replace("{count}", str(count)).replace("{result}", str(count))
        else:
            msg = "Không tìm thấy dữ liệu phù hợp."
        return {
            "type": "TABLE",
            "message": msg,
            "total_records": count,
            "data": rows
        }
