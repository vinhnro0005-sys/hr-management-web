import os
from dotenv import load_dotenv
from google import genai
from app.modules.chatbot.policy_service import handle_policy_inquiry
from app.modules.chatbot.metric_service import handle_metric_inquiry

load_dotenv()
_ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

POLICY_KEYWORDS = [
    "nghỉ phép", "ngày phép", "phép năm", "quy chế", "nội quy",
    "khen thưởng", "kỷ luật", "thời gian làm việc", "đi muộn", "chế độ",
    "bảo hiểm", "thai sản", "sa thải", "hợp đồng", "giờ làm"
]

METRIC_KEYWORDS = [
    "bao nhiêu", "số lượng", "danh sách", "đếm", "tổng số", "mới vào",
    "nhân sự", "phòng ban", "thống kê", "liệt kê", "danh mục"
]

def classify_intent(message: str) -> str:
    """Phân loại câu hỏi thuộc POLICY (Nội quy) hay METRIC (Số liệu DB)."""
    msg_lower = (message or "").lower()

    # 1. Nhận diện tức thì bằng quy tắc từ khóa (0.001s, không tốn thời gian gọi mạng)
    for kw in POLICY_KEYWORDS:
        if kw in msg_lower:
            return "POLICY"
    for kw in METRIC_KEYWORDS:
        if kw in msg_lower:
            return "METRIC"

    # 2. Fallback sang LLM nhẹ gemini-3.5-flash-lite nếu câu hỏi mơ hồ
    prompt = f"""
    Phân loại câu hỏi sau:
    - 'POLICY': Hỏi về quy chế, nội quy, ngày phép, khen thưởng, kỷ luật, chế độ.
    - 'METRIC': Hỏi số lượng, danh sách nhân viên, đếm người, dữ liệu nhân sự.
    Câu hỏi: "{message}"
    Chỉ trả về đúng một từ 'POLICY' hoặc 'METRIC'.
    """
    try:
        resp = _ai_client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
        return resp.text.strip().upper()
    except Exception:
        return "METRIC"

def process_chat_message(user_message: str) -> dict:
    """Hàm điều phối trung tâm."""
    intent = classify_intent(user_message)
    
    if "POLICY" in intent:
        return handle_policy_inquiry(user_message)
    else:
        return handle_metric_inquiry(user_message)
