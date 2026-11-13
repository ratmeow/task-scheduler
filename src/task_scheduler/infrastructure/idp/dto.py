from dataclasses import dataclass


@dataclass
class TokenDTO:
    token_hash: str
    user_id: str
    ttl: int
