import aiosmtplib
from email.message import EmailMessage
from typing import List, Optional
from src.common.config import settings


def get_email_base_template(content: str, preview_text: str = "") -> str:
    """
    Returns the base HTML email template with Kliniq dark mode styling.
    
    Args:
        content: The main content HTML to insert into the template.
        preview_text: Preview text shown in email clients.
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Kliniq</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, sans-serif !important;}}
    </style>
    <![endif]-->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <!-- Preview text -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preview_text}
    </div>
    
    <!-- Main container -->
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #0a0a0f;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Email card -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 520px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; overflow: hidden;">
                    
                    <!-- Header with logo -->
                    <tr>
                        <td style="padding: 32px 40px 24px; text-align: center; border-bottom: 1px solid rgba(99, 102, 241, 0.15);">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                <tr>
                                    <td style="width: 44px; height: 44px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 12px; text-align: center; vertical-align: middle;">
                                        <span style="color: white; font-size: 22px; font-weight: 700; line-height: 44px;">K</span>
                                    </td>
                                    <td style="padding-left: 12px;">
                                        <span style="font-size: 26px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">Kliniq</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Content area -->
                    <tr>
                        <td style="padding: 32px 40px 40px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: rgba(0, 0, 0, 0.3); border-top: 1px solid rgba(99, 102, 241, 0.15);">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td style="text-align: center;">
                                        <p style="margin: 0 0 8px; font-size: 13px; color: #71717a;">
                                            AI-Powered Clinical Communication
                                        </p>
                                        <p style="margin: 0 0 16px; font-size: 12px; color: #52525b;">
                                            © 2024 Kliniq. All rights reserved.
                                        </p>
                                        <p style="margin: 0; font-size: 11px; color: #3f3f46;">
                                            <a href="{settings.FRONTEND_URL}" style="color: #6366f1; text-decoration: none;">Visit Website</a>
                                            <span style="color: #3f3f46; margin: 0 8px;">•</span>
                                            <a href="{settings.SUPPORT_URL}" style="color: #6366f1; text-decoration: none;">Get Support</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_verification_email_html(first_name: str, verification_link: str, verification_code: str) -> str:
    """Generate the verification email HTML content."""
    content = f"""
        <h1 style="margin: 0 0 8px; font-size: 24px; font-weight: 700; color: #fafafa; text-align: center;">
            Welcome to Kliniq! 👋
        </h1>
        <p style="margin: 0 0 28px; font-size: 15px; color: #a1a1aa; text-align: center; line-height: 1.6;">
            You're one step away from accessing smarter healthcare.
        </p>
        
        <p style="margin: 0 0 20px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Hi <strong style="color: #fafafa;">{first_name}</strong>,
        </p>
        <p style="margin: 0 0 28px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Thanks for signing up! Please verify your email address to activate your account and start your journey with us.
        </p>
        
        <!-- Primary CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 8px 0 28px;">
                    <a href="{verification_link}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 10px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);">
                        Verify Email Address
                    </a>
                </td>
            </tr>
        </table>
        
        <!-- Divider -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 0 0 24px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                        <tr>
                            <td style="border-top: 1px solid rgba(99, 102, 241, 0.2);"></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <p style="margin: 0 0 12px; font-size: 13px; color: #71717a; text-align: center;">
            Or enter this verification code manually:
        </p>
        
        <!-- Verification Code Box -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 0 0 28px;">
                    <div style="display: inline-block; background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); padding: 16px 32px; border-radius: 12px;">
                        <span style="font-size: 28px; font-weight: 700; letter-spacing: 6px; color: #a78bfa; font-family: 'Courier New', monospace;">{verification_code}</span>
                    </div>
                </td>
            </tr>
        </table>
        
        <!-- Warning notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.2); border-radius: 8px;">
            <tr>
                <td style="padding: 12px 16px;">
                    <p style="margin: 0; font-size: 12px; color: #fbbf24; line-height: 1.5;">
                        ⏰ This verification link expires in <strong>24 hours</strong>. If you didn't create an account, please ignore this email.
                    </p>
                </td>
            </tr>
        </table>
    """
    return get_email_base_template(content, "Verify your Kliniq account to get started")


def get_password_reset_email_html(first_name: str, reset_link: str) -> str:
    """Generate the password reset request email HTML content."""
    content = f"""
        <h1 style="margin: 0 0 8px; font-size: 24px; font-weight: 700; color: #fafafa; text-align: center;">
            Reset Your Password 🔐
        </h1>
        <p style="margin: 0 0 28px; font-size: 15px; color: #a1a1aa; text-align: center; line-height: 1.6;">
            We received a request to reset your password.
        </p>
        
        <p style="margin: 0 0 20px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Hi <strong style="color: #fafafa;">{first_name}</strong>,
        </p>
        <p style="margin: 0 0 28px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Someone requested a password reset for your Kliniq account. If this was you, click the button below to create a new password.
        </p>
        
        <!-- Primary CTA Button -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td align="center" style="padding: 8px 0 28px;">
                    <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 10px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);">
                        Reset Password
                    </a>
                </td>
            </tr>
        </table>
        
        <!-- Warning notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.2); border-radius: 8px;">
            <tr>
                <td style="padding: 12px 16px;">
                    <p style="margin: 0; font-size: 12px; color: #fbbf24; line-height: 1.5;">
                        ⏰ This link expires in <strong>30 minutes</strong>. If you didn't request this reset, please ignore this email — your password will remain unchanged.
                    </p>
                </td>
            </tr>
        </table>
        
        <!-- Security tip -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-top: 20px;">
            <tr>
                <td style="padding: 16px; background: rgba(99, 102, 241, 0.05); border-radius: 8px; border-left: 3px solid #6366f1;">
                    <p style="margin: 0; font-size: 12px; color: #71717a; line-height: 1.5;">
                        🛡️ <strong style="color: #a1a1aa;">Security tip:</strong> Kliniq will never ask for your password via email or phone. If you receive suspicious messages, please report them to our support team.
                    </p>
                </td>
            </tr>
        </table>
    """
    return get_email_base_template(content, "Reset your Kliniq password")


def get_password_reset_confirmation_html(first_name: str, support_url: str) -> str:
    """Generate the password reset confirmation email HTML content."""
    content = f"""
        <h1 style="margin: 0 0 8px; font-size: 24px; font-weight: 700; color: #fafafa; text-align: center;">
            Password Changed ✅
        </h1>
        <p style="margin: 0 0 28px; font-size: 15px; color: #a1a1aa; text-align: center; line-height: 1.6;">
            Your account security has been updated.
        </p>
        
        <p style="margin: 0 0 20px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Hi <strong style="color: #fafafa;">{first_name}</strong>,
        </p>
        <p style="margin: 0 0 28px; font-size: 15px; color: #d4d4d8; line-height: 1.7;">
            Your password has been successfully changed. You can now use your new password to sign in to your Kliniq account.
        </p>
        
        <!-- Success indicator -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 24px;">
            <tr>
                <td align="center">
                    <div style="display: inline-block; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); padding: 16px 24px; border-radius: 12px;">
                        <span style="font-size: 14px; color: #4ade80;">
                            ✓ Password updated successfully
                        </span>
                    </div>
                </td>
            </tr>
        </table>
        
        <!-- Warning notice -->
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px;">
            <tr>
                <td style="padding: 16px;">
                    <p style="margin: 0 0 12px; font-size: 13px; color: #f87171; font-weight: 600;">
                        ⚠️ Didn't make this change?
                    </p>
                    <p style="margin: 0 0 16px; font-size: 12px; color: #fca5a5; line-height: 1.5;">
                        If you didn't reset your password, someone may have access to your account. Please take action immediately:
                    </p>
                    <a href="{support_url}" style="display: inline-block; background: rgba(239, 68, 68, 0.2); color: #f87171; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 13px; border: 1px solid rgba(239, 68, 68, 0.3);">
                        Contact Support
                    </a>
                </td>
            </tr>
        </table>
    """
    return get_email_base_template(content, "Your Kliniq password has been changed")


async def send_email(subject: str, body: str, recipients: List[str], html_body: Optional[str] = None) -> None:
    """
    Sends an email asynchronously using aiosmtplib.
    
    Args:
        subject (str): The subject of the email.
        body (str): The plain text content of the email.
        recipients (List[str]): List of recipient email addresses.
        html_body (Optional[str]): HTML content of the email.
    """
    message = EmailMessage()
    message["From"] = settings.EMAIL_SENDER
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

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

    plain_text = f"""
Hi {first_name},

Welcome to Kliniq! Please verify your email address to activate your account.

Click the following link to verify your email:
{verification_link}

Or enter this verification code manually: {verification_code}

This link expires in 24 hours. If you didn't create an account, please ignore this email.

Best regards,
The Kliniq Team
"""

    html_content = get_verification_email_html(first_name, verification_link, verification_code)
    
    await send_email("Verify your Kliniq account", plain_text, [recipient_email], html_body=html_content)


async def send_password_reset_email(recipient_email: str, first_name: str, reset_link: str) -> None:
    """
    Sends a password reset email to the specified recipient.
    
    Args:
        recipient_email (str): The email address of the recipient.
        first_name (str): The first name of the user.
        reset_link (str): The password reset link.
    """
    plain_text = f"""
Hi {first_name},

Someone requested a password reset for your Kliniq account.

Click the following link to reset your password:
{reset_link}

This link expires in 30 minutes. If you didn't request this reset, please ignore this email.

Best regards,
The Kliniq Team
"""

    html_content = get_password_reset_email_html(first_name, reset_link)
    
    await send_email("Reset your Kliniq password", plain_text, [recipient_email], html_body=html_content)


async def send_password_reset_confirmation_email(recipient_email: str, first_name: str) -> None:
    """
    Sends a password reset confirmation email to the specified recipient.
    
    Args:
        recipient_email (str): The email address of the recipient.
        first_name (str): The first name of the user.
    """
    plain_text = f"""
Hi {first_name},

Your password has been successfully changed. You can now use your new password to sign in to your Kliniq account.

If you didn't make this change, please contact support immediately at {settings.SUPPORT_URL}

Best regards,
The Kliniq Team
"""

    html_content = get_password_reset_confirmation_html(first_name, settings.SUPPORT_URL)
    
    await send_email("Your Kliniq password has been changed", plain_text, [recipient_email], html_body=html_content)
