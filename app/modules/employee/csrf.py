from fastapi import HTTPException, Request

from app.modules.auth.security import verify_csrf_token

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def require_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    form = await request.form()
    if not verify_csrf_token(request.session.get("csrf_token"), str(form.get("csrf_token", ""))):
        raise HTTPException(
            status_code=403,
            detail="Phiên làm việc đã hết hạn hoặc thiếu mã CSRF. Hãy tải lại trang rồi thử lại.",
        )