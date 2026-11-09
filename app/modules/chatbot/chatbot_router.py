from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.modules.auth.dependencies import get_current_user
from app.modules.chatbot.chatbot_service import process_chat_message

router = APIRouter(
    prefix="/chat",
    tags=["AI Chatbot"],
    dependencies=[Depends(get_current_user)],
)
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def chat_page(request: Request, user = Depends(get_current_user)):
    """Trang giao diện chuyên dụng cho AI Chatbot."""
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "user": user,
            "page_title": "Trợ lý AI Nhân sự"
        }
    )

@router.post("/message")
async def chat_message_html(request: Request, message: str = Form(None)):
    """Xử lý câu hỏi và trả về component HTML partial (chat_bubble.html)."""
    user_message = message
    if not user_message:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                user_message = body.get("message")
            except Exception:
                pass
    if not user_message:
        user_message = request.query_params.get("message", "")

    user_message = (user_message or "").strip()
    if not user_message:
        result = {
            "type": "TEXT",
            "message": "Vui lòng nhập nội dung câu hỏi.",
            "data": None,
            "citation": None,
            "total_records": 0
        }
    else:
        # 1. Gọi service điều phối lấy kết quả nghiệp vụ
        try:
            result = process_chat_message(user_message)
        except Exception as e:
            import traceback
            traceback.print_exc()
            result = {
                "type": "ERROR",
                "message": f"Hệ thống tạm thời không thể xử lý câu hỏi này: {str(e)}",
                "data": None,
                "citation": None,
                "total_records": 0
            }

    # 2. Render trực tiếp mảnh HTML (bắt buộc dùng request=request, name=... ở FastAPI/Starlette mới)
    return templates.TemplateResponse(
        request=request,
        name="components/chat_bubble.html",
        context={
            "user_message": user_message,
            "type": result.get("type", "TEXT"),
            "message": result.get("message", ""),
            "data": result.get("data"),
            "citation": result.get("citation"),
            "total_records": result.get("total_records", 0)
        }
    )

@router.post("/api/message")
async def chat_message_json(request: Request, message: str = Form(None)):
    """API endpoint trả dữ liệu JSON thô."""
    user_message = message
    if not user_message:
        try:
            body = await request.json()
            user_message = body.get("message")
        except Exception:
            pass
    if not user_message:
        user_message = request.query_params.get("message", "")

    user_message = (user_message or "").strip()
    if not user_message:
        return JSONResponse({
            "type": "TEXT",
            "message": "Vui lòng nhập nội dung câu hỏi.",
            "data": None,
            "citation": None,
            "total_records": 0
        })

    result = process_chat_message(user_message)
    return JSONResponse(result)