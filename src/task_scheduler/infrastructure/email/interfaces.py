from typing import Protocol


class Sender(Protocol):
    async def send(self, recipient: str, subject: str, text: str) -> None:
        pass
