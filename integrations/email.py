
"""
Email integration using SMTP.

Sends customer support emails using the application's
configured SMTP credentials.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from config import settings


logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


# ============================================================
# Validation
# ============================================================

def _validate_email_inputs(
    to: str,
    subject: str,
    body: str,
) -> None:
    """Validate email inputs and prevent header injection."""

    if not isinstance(to, str) or not to.strip():
        raise ValueError("Recipient email cannot be empty.")

    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Email subject cannot be empty.")

    if not isinstance(body, str) or not body.strip():
        raise ValueError("Email body cannot be empty.")

    # Prevent newline characters from injecting email headers.
    if "\r" in to or "\n" in to:
        raise ValueError("Invalid recipient email.")

    if "\r" in subject or "\n" in subject:
        raise ValueError("Invalid email subject.")


def _validate_smtp_configuration() -> None:
    """Ensure the required SMTP settings are configured."""

    if not settings.EMAIL_HOST or not settings.EMAIL_HOST.strip():
        raise RuntimeError("EMAIL_HOST is not configured.")

    if (
        not isinstance(settings.EMAIL_PORT, int)
        or isinstance(settings.EMAIL_PORT, bool)
        or not 1 <= settings.EMAIL_PORT <= 65535
    ):
        raise RuntimeError("EMAIL_PORT is invalid.")

    if (
        not settings.EMAIL_USERNAME
        or not settings.EMAIL_USERNAME.strip()
    ):
        raise RuntimeError("EMAIL_USERNAME is not configured.")

    if not settings.EMAIL_PASSWORD:
        raise RuntimeError("EMAIL_PASSWORD is not configured.")


# ============================================================
# Email Message
# ============================================================

def _build_message(
    to: str,
    subject: str,
    body: str,
) -> EmailMessage:
    """Build a plain-text email message."""

    message = EmailMessage()
    message["From"] = settings.EMAIL_USERNAME.strip()
    message["To"] = to.strip()
    message["Subject"] = subject.strip()
    message.set_content(body.strip())

    return message


# ============================================================
# Send Email
# ============================================================

def send_email(
    to: str,
    subject: str,
    body: str,
) -> bool:
    """
    Send an email through the configured SMTP server.

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Plain-text email body.

    Returns:
        True if the SMTP server accepts the message.

    Raises:
        ValueError: If the input is invalid.
        RuntimeError: If SMTP configuration or delivery fails.
    """

    _validate_email_inputs(to, subject, body)
    _validate_smtp_configuration()

    message = _build_message(to, subject, body)

    try:
        with smtplib.SMTP(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()

            smtp.login(
                settings.EMAIL_USERNAME,
                settings.EMAIL_PASSWORD,
            )

            smtp.send_message(message)

        logger.info("Email sent successfully.")
        return True

    except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
        # Avoid logging SMTP exception text because it may contain
        # server details or other information we don't need to expose.
        logger.error(
            "Email delivery failed. Error type: %s",
            type(exc).__name__,
        )

        raise RuntimeError("Unable to send email.") from exc
