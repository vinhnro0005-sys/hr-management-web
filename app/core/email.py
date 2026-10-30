import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

# Nạp thư mục templates của ứng dụng
jinja_env = Environment(loader=FileSystemLoader("app/templates"))


def send_email(to_email: str, subject: str, template_name: str, context: dict) -> bool:
    """
    Hàm gửi email dùng chung:
    - to_email: Địa chỉ người nhận
    - subject: Tiêu đề thư
    - template_name: Đường dẫn template trong thư mục templates (vd: emails/welcome_account.html)
    - context: Dữ liệu truyền vào template (dict)
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("Chưa cấu hình SMTP_USER hoặc SMTP_PASSWORD trong .env. Bỏ qua việc gửi mail.")
        return False

    try:
        # 1. Render template HTML với dữ liệu context
        template = jinja_env.get_template(template_name)
        html_body = template.render(**context)

        # 2. Tạo đối tượng MIME
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.emails_from_name} <{settings.emails_from_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 3. Kết nối SMTP Gmail và gửi
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()  # Mã hóa kết nối an toàn TLS
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.emails_from_email, [to_email], msg.as_string())

        logger.info(f"Đã gửi email thành công tới: {to_email}")
        return True

    except Exception as exc:
        logger.error(f"Lỗi khi gửi email tới {to_email}: {exc}")
        return False
