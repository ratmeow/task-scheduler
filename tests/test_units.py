import pytest
from task_scheduler.domain.entities import User
from task_scheduler.domain.exceptions import DomainError

class TestUser:
    def test_create(self):
        user = User(login="ratmeow", hashed_password="289sdyf87sf")
        assert user.login == "ratmeow"
        assert user.id is not None

    def test_invalid_login(self):
        with pytest.raises(DomainError, match="Login must be"):
            User(login="ba", hashed_password="79df8gd")
