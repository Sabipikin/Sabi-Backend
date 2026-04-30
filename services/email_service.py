import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with templates"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@sabieducate.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.sender_name = os.getenv("SENDER_NAME", "Sabi Educate")

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates" / "emails"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email using a template

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template file (e.g., 'payment_confirmation.html')
            context: Dictionary of variables to pass to the template
            cc: List of CC email addresses
            bcc: List of BCC email addresses

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Render template
            template = self.env.get_template(template_name)
            html_content = template.render(**context)

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email

            if cc:
                message["Cc"] = ", ".join(cc)

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Prepare recipients list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, message.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_payment_confirmation(
        self, user_email: str, user_name: str, payment_data: dict
    ) -> bool:
        """Send payment confirmation email"""
        context = {
            "user_name": user_name,
            "payment_id": payment_data.get("id"),
            "amount": f"{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}",
            "item_type": payment_data.get("item_type", "").title(),
            "item_name": payment_data.get("item_name", ""),
            "order_date": datetime.fromisoformat(
                payment_data.get("created_at", datetime.now().isoformat())
            ).strftime("%B %d, %Y at %H:%M"),
            "order_id": payment_data.get("payoneer_order_id", ""),
            "dashboard_url": os.getenv("FRONTEND_URL", "https://app.sabieducate.com"),
            "support_email": os.getenv("SUPPORT_EMAIL", "support@sabieducate.com"),
        }

        return self.send_email(
            to_email=user_email,
            subject=f"Payment Confirmation - Order #{payment_data.get('id')}",
            template_name="payment_confirmation.html",
            context=context,
        )

    def send_payment_receipt(
        self, user_email: str, user_name: str, payment_data: dict, pdf_path: Optional[str] = None
    ) -> bool:
        """Send payment receipt email with optional PDF attachment"""
        context = {
            "user_name": user_name,
            "payment_id": payment_data.get("id"),
            "amount": f"{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}",
            "item_type": payment_data.get("item_type", "").title(),
            "item_name": payment_data.get("item_name", ""),
            "order_date": datetime.fromisoformat(
                payment_data.get("created_at", datetime.now().isoformat())
            ).strftime("%B %d, %Y"),
            "order_id": payment_data.get("payoneer_order_id", ""),
            "completed_date": datetime.fromisoformat(
                payment_data.get("completed_at", datetime.now().isoformat())
            ).strftime("%B %d, %Y at %H:%M"),
            "dashboard_url": os.getenv("FRONTEND_URL", "https://app.sabieducate.com"),
            "support_email": os.getenv("SUPPORT_EMAIL", "support@sabieducate.com"),
        }

        return self.send_email(
            to_email=user_email,
            subject=f"Payment Receipt - Order #{payment_data.get('id')}",
            template_name="payment_receipt.html",
            context=context,
        )

    def send_refund_notification(
        self, user_email: str, user_name: str, payment_data: dict
    ) -> bool:
        """Send refund notification email"""
        context = {
            "user_name": user_name,
            "payment_id": payment_data.get("id"),
            "amount": f"{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}",
            "item_type": payment_data.get("item_type", "").title(),
            "item_name": payment_data.get("item_name", ""),
            "order_id": payment_data.get("payoneer_order_id", ""),
            "refund_date": datetime.now().strftime("%B %d, %Y at %H:%M"),
            "support_email": os.getenv("SUPPORT_EMAIL", "support@sabieducate.com"),
        }

        return self.send_email(
            to_email=user_email,
            subject=f"Refund Processed - Order #{payment_data.get('id')}",
            template_name="refund_notification.html",
            context=context,
        )
