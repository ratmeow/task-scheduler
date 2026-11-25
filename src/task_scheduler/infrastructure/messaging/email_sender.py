import httpx

from task_scheduler.config import EmailClientConfig


class ResendEmailSender:
    def __init__(
        self,
        client: httpx.Client,
        config: EmailClientConfig,
    ) -> None:
        self._client = client
        self.config = config

    def send(self, email: str, text: str) -> str:
        response = self._client.post(
            self.config.url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
            },
            json={
                "from": self.config.sender,
                "to": [email],
                "subject": "Task Scheduler",
                "html": f"<h1>{text}!</h1>",
            },
        )
        response.raise_for_status()

        return response.json()["id"]
