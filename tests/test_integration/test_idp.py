import pytest

from task_scheduler.application.exceptions import ApplicationError
from task_scheduler.infrastructure.idp.interfaces import TokenStorage
from task_scheduler.infrastructure.idp.provider import IdentityProvider


class TestRefreshToken:
    async def test_create(self, idp: IdentityProvider, token_storage: TokenStorage):
        user_id = "123"

        token = await idp.create_refresh_token(user_id=user_id)
        token_hash = idp.hash_token(token=token)
        user_id_from_storage = await token_storage.get(token_key=token_hash)
        assert user_id_from_storage is not None
        assert user_id == user_id_from_storage

    async def test_delete(self, idp: IdentityProvider, token_storage: TokenStorage):
        user_id = "123"
        token = await idp.create_refresh_token(user_id=user_id)

        await idp.delete_refresh_token(token=token)
        with pytest.raises(ApplicationError):
            await token_storage.get(token_key=idp.hash_token(token=token))

    async def test_rotate(self, idp: IdentityProvider, token_storage: TokenStorage):
        user_id = "123"
        token = await idp.create_refresh_token(user_id=user_id)

        new_token = await idp.rotate_refresh_token(token=token)
        assert new_token is not None
        assert token != new_token
