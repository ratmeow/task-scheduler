from typing import Protocol


class EmailPublisher(Protocol):
    async def publish(self, email: str, text: str) -> str:
        pass
