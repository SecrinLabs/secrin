from pathlib import Path
from typing import Dict
from mails.types import MailType
from mails.template_vars import TEMPLATE_VARS

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
