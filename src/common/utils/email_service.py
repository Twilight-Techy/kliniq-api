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
async def send_verification_email(recipient_email: str, first_name: str, verification_code: str) -> None:
    """
    Sends a verification email to the specified recipient.
    
    Args:
        recipient_email (str): The email address of the recipient.
        first_name (str): The first name of the user.
        verification_code (str): The code for the verification.
    """
    import urllib.parse
    encoded_email = urllib.parse.quote(recipient_email)
    verification_link = f"{settings.FRONTEND_URL}/auth/verify?code={verification_code}&email={encoded_email}"

    email_content = f"""
Dear {first_name},

Welcome to Kliniq! Please verify your email address to activate your account.

Click the following link to verify your email:
{verification_link}

Or enter this verification code manually: {verification_code}

If you did not create an account, please ignore this email.

Best regards,
The Kliniq Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Kliniq!</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
        <p style="font-size: 16px;">Dear <strong>{first_name}</strong>,</p>
        <p style="font-size: 16px;">Thank you for signing up! Please verify your email address to activate your account.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">Verify Email Address</a>
        </div>
        
        <p style="font-size: 14px; color: #6b7280;">Or enter this code manually:</p>
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; text-align: center; margin: 16px 0;">
            <code style="font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #6366f1;">{verification_code}</code>
        </div>
        
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="font-size: 12px; color: #9ca3af; text-align: center;">
            If you did not create an account, please ignore this email.<br>
            This link will expire in 24 hours.
        </p>
    </div>
</body>
</html>
"""

    await send_email("Verify your Kliniq account", email_content, [recipient_email], html_body=html_content)



