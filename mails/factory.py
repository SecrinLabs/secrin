from pathlib import Path
from typing import Dict
from email.mime.text import MIMEText
import smtplib

from mails.types import MailType
from mails.template_vars import TEMPLATE_VARS
from config import settings, get_logger

logger = get_logger(__name__)

class EmailFactory:
    TEMPLATES_DIR = Path(__file__).parent / "templates"

    @staticmethod
    def get_template(mail_type: MailType) -> str:
        template_file = EmailFactory.TEMPLATES_DIR / f"{mail_type.value}.html"
        if not template_file.exists():
            raise FileNotFoundError(f"Template for {mail_type.value} not found.")
        return template_file.read_text()

    @staticmethod
    def render(mail_type: MailType, variables: Dict[str, str]) -> str:
        required_vars = TEMPLATE_VARS.get(mail_type, [])
        missing = [v for v in required_vars if v not in variables]
        if missing:
            raise ValueError(f"Missing variables for {mail_type.value}: {missing}")

        template = EmailFactory.get_template(mail_type)
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", value)
        return template
    
    @staticmethod
    def send(mail_type: MailType, to_email: str, variables: Dict[str, str], subject: str = None):
        """
        Render template and send email via SMTP.
        """
        html_body = EmailFactory.render(mail_type, variables)
        email_subject = subject or f"{mail_type.value} Notification"

        msg = MIMEText(html_body, "html")
        msg["Subject"] = email_subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email

        print(html_body, email_subject)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
            logger.info(f"Email sent to {to_email} with subject '{email_subject}'")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)