"""Best-effort SMTP delivery. Never log tokens, addresses or SMTP credentials."""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_account_mail(recipient: str, token: str, purpose: str) -> None:
    verify = purpose == "verify"
    title = "Xác minh email STOCKPULSE" if verify else "Đặt lại mật khẩu STOCKPULSE"
    route = "verify-email" if verify else "reset-password"
    lifetime = "24 giờ" if verify else "30 phút"
    url = f"{settings.FRONTEND_PUBLIC_URL.rstrip('/')}/{route}#token={token}"
    message = EmailMessage()
    message["Subject"] = title
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    message["To"] = recipient
    text = f"{title}\n\nMở liên kết: {url}\nLiên kết dùng một lần, hiệu lực {lifetime}. Nếu bạn không yêu cầu, hãy bỏ qua thư này."
    message.set_content(text)
    message.add_alternative(
        f'<h1>{title}</h1><p><a href="{escape(url, quote=True)}">{title}</a></p><p>Liên kết dùng một lần, hiệu lực {lifetime}. Nếu bạn không yêu cầu, hãy bỏ qua thư này.</p>',
        subtype="html",
    )
    try:
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            raise ValueError("SMTP not configured")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("Account mail delivered (%s)", purpose)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.warning("Account mail delivery failed (%s); user may request a new link", purpose)
