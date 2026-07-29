import re
from .interfaces import Hasher, UserGateway, DBSession
from .dto import UserRegisterData
from task_scheduler.domain.entities import User
from .exceptions import PasswordRequirementError, AlreadyExistsError, UserNotFoundError, WrongPasswordError

class RegisterUserInteractor:
    def __init__(self, user_gateway: UserGateway, hasher: Hasher, db_session: DBSession):
        self.user_gateway = user_gateway
        self.hasher = hasher
        self.db_session = db_session

    async def __call__(self, register_data: UserRegisterData) -> str:
        if not self._is_strong_password(password=register_data.password):
            raise PasswordRequirementError()

        user = User(login=register_data.login, hashed_password=self.hasher.hash(text=register_data.password))

        if await self.user_gateway.get_by_login(login=register_data.login) is not None:
            raise AlreadyExistsError()

        await self.user_gateway.save(user=user)
        await self.db_session.commit()
        return str(user.id)

    @staticmethod
    def _is_strong_password(password: str) -> bool:
        pattern = r"^[A-Za-z\d!@#$%^&*_]{8,}$"
        has_required_char = bool(re.search(r"[\d!@#$%^&*_]", password))
        return bool(re.fullmatch(pattern, password)) and has_required_char


class LoginUserInteractor:
    def __init__(self, user_gateway: UserGateway, hasher: Hasher):
        self.user_gateway = user_gateway
        self.hasher = hasher

    async def __call__(self, login_data: UserRegisterData) -> str:
        exist_user = await self.user_gateway.get_by_login(login=login_data.login)
        if not exist_user:
            raise UserNotFoundError(info=login_data.login)

        if not self.hasher.verify_hash(original_text=login_data.password, hashed_text=exist_user.hashed_password):
            raise WrongPasswordError()
        return str(exist_user.id)
