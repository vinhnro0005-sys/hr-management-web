from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
from pathlib import Path
import smtplib
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings

logger = logging.getLogger(__name__)

# Nạp thư mục templates của ứng dụng bằng đường dẫn tuyệt đối an toàn
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def send_email(to_email: str, subject: str, template_name: str, context: dict) -> bool:
    """
    Hàm gửi email dùng chung:
    - to_email: Địa chỉ người nhận
    - subject: Tiêu đề thư
    - template_name: Đường dẫn template trong thư mục templates (vd: emails/reset_password.html)
    - context: Dữ liệu truyền vào template (dict)
    """
    smtp_user = (settings.smtp_user or "").strip()
    smtp_password = (settings.smtp_password or "").replace(" ", "").strip()

    if not smtp_user or not smtp_password:
        msg = "Chưa cấu hình SMTP_USER hoặc SMTP_PASSWORD trong .env. Bỏ qua việc gửi mail."
        logger.warning(msg)
        print(f"[EMAIL WARNING] {msg}")
        return False

    try:
        # 1. Render template HTML với dữ liệu context
        template = jinja_env.get_template(template_name)
        html_body = template.render(**context)

        # 2. Tạo đối tượng MIME chuẩn RFC 2047 hỗ trợ tiêu đề và tên tiếng Việt
        from_email = (settings.emails_from_email or smtp_user).strip()
        from_name = (settings.emails_from_name or "Phòng Nhân Sự HR").strip().strip('"').strip("'")
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(from_name, "utf-8")), from_email))
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 3. Kết nối SMTP Gmail và gửi an toàn
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()  # Mã hóa kết nối an toàn TLS
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, [to_email], msg.as_string())

        logger.info(f"Đã gửi email thành công tới: {to_email}")
        print(f"[EMAIL SUCCESS] Đã gửi email thành công tới: {to_email}")
        return True

    except Exception as exc:
        err_msg = f"Lỗi khi gửi email tới {to_email}: {exc}"
        logger.error(err_msg)
        print(f"[EMAIL ERROR] {err_msg}")
        return False
