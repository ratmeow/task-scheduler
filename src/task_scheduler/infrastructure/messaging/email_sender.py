from email.message import EmailMessage
from smtplib import SMTP_SSL

from task_scheduler.config import EmailClientConfig


class ResendEmailSender:
    def __init__(
        self,
        client: SMTP_SSL,
        config: EmailClientConfig,
    ) -> None:
        self._client = client
        self.config = config

    def send(self, email: str, text: str) -> None:
        message = EmailMessage()
        message["From"] = self.config.sender
        message["To"] = email
        message["Subject"] = "Task Scheduler"
        message.set_content(f"<h1>{text}!</h1>", subtype="html")
        self._client.send_message(message)
