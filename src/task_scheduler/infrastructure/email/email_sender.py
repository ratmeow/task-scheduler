import httpx

from task_scheduler.config import EmailClientConfig


class MailjetEmailSender:
    def __init__(self, config: EmailClientConfig):
        self.url = config.url
        self.auth = (config.api_key, config.secret_key)
        self.sender = config.sender
        self.sender_name = config.sender_name

    async def send(
        self,
        recipient: str,
        subject: str,
        text: str,
    ) -> None:
        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": self.sender,
                        "Name": "Etobaza",
                    },
                    "To": [
                        {"Email": recipient},
                    ],
                    "Subject": subject,
                    "TextPart": text,
                }
            ]
        }

        async with httpx.AsyncClient(
            timeout=10.0,
            auth=self.auth,
        ) as client:
            response = await client.post(
                self.url,
                json=payload,
            )
            response.raise_for_status()
