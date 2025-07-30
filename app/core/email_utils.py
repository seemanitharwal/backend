import logging, smtplib
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger(__name__)


SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USERNAME = settings.smtp_username
SMTP_PASSWORD = settings.smtp_password
FROM_EMAIL = settings.from_email or (SMTP_USERNAME or "noreply@example.com")
USE_TLS = settings.smtp_use_tls


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


def send_verification_email(to_email: str, verification_link: str) -> None:
    """Send employee verification email.
    If SMTP is not configured, log instructions instead of raising.
    """
    subject = "Verify your Mercor Time Tracker account"
    body = (
        f"Hello,\n\n"
        f"Thank you for registering with Mercor Time Tracker. "
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        f"If you did not create an account, please ignore this email.\n\n"
        f"Regards,\nMercor Team"
    )

    if not _smtp_configured():
        # Fallback: Log the verification link so it can still be accessed in dev environments.
        logger.warning(
            "SMTP not configured. Email NOT sent. Verification link for %s: %s",
            to_email,
            verification_link,
        )
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if USE_TLS:
                server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Sent verification email to %s", to_email)
    except Exception as e:
        logger.exception("Failed to send verification email to %s: %s", to_email, e) 