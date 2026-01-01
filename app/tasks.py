import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv

from app.celery_app import celery_app

load_dotenv()

# Email configuration (you can move this to environment variables)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_email_sync(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Synchronous function to send email via SMTP
    This will be called by the Celery task
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        # Add plain text and HTML versions
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)

        if html_body:
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

        # For demo purposes, if SMTP is not configured, just print
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"[DEMO EMAIL] To: {to_email}")
            print(f"[DEMO EMAIL] Subject: {subject}")
            print(f"[DEMO EMAIL] Body: {body}")
            return True

        # Send email via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


@celery_app.task(name="app.tasks.send_welcome_email")
def send_welcome_email(user_email: str, user_id: int) -> dict:
    """
    Celery task to send welcome email to new users
    This runs asynchronously in the background
    """
    subject = "Welcome to Our Platform!"
    body = f"""
    Hello!

    Thank you for joining our platform. Your account has been successfully created.

    User ID: {user_id}
    Email: {user_email}

    We're excited to have you on board!

    Best regards,
    The Team
    """
    html_body = f"""
    <html>
      <body>
        <h2>Welcome to Our Platform!</h2>
        <p>Hello!</p>
        <p>Thank you for joining our platform. Your account has been successfully created.</p>
        <ul>
          <li><strong>User ID:</strong> {user_id}</li>
          <li><strong>Email:</strong> {user_email}</li>
        </ul>
        <p>We're excited to have you on board!</p>
        <p>Best regards,<br>The Team</p>
      </body>
    </html>
    """

    success = send_email_sync(user_email, subject, body, html_body)
    return {
        "status": "success" if success else "failed",
        "email": user_email,
        "task": "welcome_email"
    }


@celery_app.task(name="app.tasks.send_order_confirmation_email")
def send_order_confirmation_email(
    user_email: str,
    order_id: int,
    total_amount: float,
    items_count: int
) -> dict:
    """
    Celery task to send order confirmation email
    This runs asynchronously in the background
    """
    subject = f"Order Confirmation - Order #{order_id}"
    body = f"""
    Hello!

    Thank you for your order. We've received it and are processing it now.

    Order Details:
    - Order ID: {order_id}
    - Total Amount: ${total_amount:.2f}
    - Number of Items: {items_count}

    We'll send you another email once your order ships.

    Best regards,
    The Team
    """
    html_body = f"""
    <html>
      <body>
        <h2>Order Confirmation</h2>
        <p>Hello!</p>
        <p>Thank you for your order. We've received it and are processing it now.</p>
        <h3>Order Details:</h3>
        <ul>
          <li><strong>Order ID:</strong> {order_id}</li>
          <li><strong>Total Amount:</strong> ${total_amount:.2f}</li>
          <li><strong>Number of Items:</strong> {items_count}</li>
        </ul>
        <p>We'll send you another email once your order ships.</p>
        <p>Best regards,<br>The Team</p>
      </body>
    </html>
    """

    success = send_email_sync(user_email, subject, body, html_body)
    return {
        "status": "success" if success else "failed",
        "email": user_email,
        "order_id": order_id,
        "task": "order_confirmation_email"
    }


@celery_app.task(name="app.tasks.send_custom_email")
def send_custom_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> dict:
    """
    Generic Celery task to send custom email
    """
    success = send_email_sync(to_email, subject, body, html_body)
    return {
        "status": "success" if success else "failed",
        "email": to_email,
        "subject": subject,
        "task": "custom_email"
    }

