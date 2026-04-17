import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.core.settings import settings


def build_verification_url(token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/login?verify_token={quote(token)}"


def send_verification_email(to_email: str, token: str) -> None:
    host = settings.smtp_host
    from_email = settings.smtp_from_email
    if not host or not from_email:
        raise RuntimeError(
            "SMTP is not configured. Set TRAINERAPP_SMTP_HOST and TRAINERAPP_SMTP_FROM_EMAIL."
        )

    verify_url = build_verification_url(token)

    message = EmailMessage()
    message["Subject"] = "Ověření e-mailu v Trainer App"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(
        "Dobrý den,\n\n"
        "děkujeme za registraci do Trainer App.\n"
        "Pro aktivaci účtu klikněte na ověřovací odkaz:\n\n"
        f"{verify_url}\n\n"
        "Pokud jste registraci neprováděl/a, tento e-mail ignorujte.\n"
    )

    smtp = smtplib.SMTP(host, settings.smtp_port, timeout=15)
    try:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
    finally:
        smtp.quit()
