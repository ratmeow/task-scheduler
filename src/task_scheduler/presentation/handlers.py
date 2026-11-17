from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Cookie, Form, Response
from starlette.responses import JSONResponse

from task_scheduler.application.dto import UserLoginData, UserRegisterData
from task_scheduler.application.interactors import (
    LoginUserInteractor,
    RegisterUserInteractor,
)
from task_scheduler.infrastructure.idp.provider import IdentityProvider

from .cookie_manager import TokenCookieManager
from .exceptions import UnauthorizedError
from .schemas import UserLoginRequest, UserRegisterRequest

router = APIRouter(prefix="/api")


@router.post("/auth/sign-up")
@inject
async def register_user(data: Annotated[UserRegisterRequest, Form()], use_case: FromDishka[RegisterUserInteractor]):
    await use_case(register_data=UserRegisterData(email=data.email, login=data.login, password=data.password))
    return Response(status_code=200)


@router.post("/auth/sign-in")
@inject
async def login_user_api(
    idp: FromDishka[IdentityProvider],
    cookie_manager: FromDishka[TokenCookieManager],
    data: Annotated[UserLoginRequest, Form()],
    use_case: FromDishka[LoginUserInteractor],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    user_id = await use_case(login_data=UserLoginData(login=data.login, password=data.password))
    access_token = idp.create_access_token(user_id=user_id)
    if refresh_token is not None:
        await idp.delete_refresh_token(token=refresh_token)
    refresh_token = await idp.create_refresh_token(user_id=user_id)

    response = JSONResponse(content={"username": data.login})
    cookie_manager.set_tokens(response=response, access_token=access_token, refresh_token=refresh_token)
    return response


@router.post("/auth/sign-out", status_code=204)
@inject
async def logout_user_api(
    idp: FromDishka[IdentityProvider],
    response: Response,
    cookie_manager: FromDishka[TokenCookieManager],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token is not None:
        await idp.delete_refresh_token(token=refresh_token)
        cookie_manager.delete_tokens(response=response)


@router.post("/auth/refresh", status_code=204)
@inject
async def refresh(
    idp: FromDishka[IdentityProvider],
    response: Response,
    cookie_manager: FromDishka[TokenCookieManager],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token is None:
        raise UnauthorizedError()

    new_refresh_token, user_id = await idp.rotate_refresh_token(token=refresh_token)
    access_token = idp.create_access_token(user_id=user_id)
    cookie_manager.set_tokens(response=response, access_token=access_token, refresh_token=new_refresh_token)


@router.get("/main")
@inject
async def main_test(idp: FromDishka[IdentityProvider], access_token: Annotated[str | None, Cookie()] = None):
    if access_token is None:
        raise UnauthorizedError()
    result = idp.validate_access_token(token=access_token)
    return f"HELLO {result} !"


# ratm1r
# RtmTest26!
