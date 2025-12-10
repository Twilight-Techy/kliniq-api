import aiosmtplib
from email.message import EmailMessage
from typing import List, Optional, TYPE_CHECKING
from src.common.config import settings  # Ensure your settings include SMTP_HOST, SMTP_PORT, etc.

async def send_email(subject: str, body: str, recipients: List[str], html_body: Optional[str] = None) -> None:
    """
    Sends an email asynchronously using aiosmtplib.
    
    Args:
        subject (str): The subject of the email.
        body (str): The plain text content of the email.
        recipients (List[str]): List of recipient email addresses.
    """
    message = EmailMessage()
    message["From"] = settings.EMAIL_SENDER
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    # If HTML content is provided, add it as an alternative.
    if html_body:
        message.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
async def send_verification_email(recipient_email: str, first_name:str, verification_code: str) -> None:
    """
    Sends a verification email to the specified recipient.
    
    Args:
        recipient_email (str): The email address of the recipient.
        first_name(str): The first name of the user.
        verification_code(str): The code for the verification.
    """
    verification_link = f"{settings.FRONTEND_URL}/auth/verify?code={verification_code}"

    email_content = f"""
Dear {first_name},

Please click the following link to verify your email: {verification_link}

Or use the following code: {verification_code}
"""
    await send_email("Email Verification", email_content, [recipient_email])



