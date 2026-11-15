from typing import Protocol

from .dto import TokenDTO


class TokenStorage(Protocol):
    async def set(self, token_data: TokenDTO) -> None:
        pass

    async def get(self, token_key: str) -> str:
        pass

    async def delete(self, token_key: str) -> None:
        pass
