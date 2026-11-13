from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Cookie, Depends, Form, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse

from task_scheduler.application.dto import UserLoginData, UserRegisterData
from task_scheduler.application.interactors import (
    LoginUserInteractor,
    RegisterUserInteractor,
)
from task_scheduler.infrastructure.idp.interfaces import IdentityProvider

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
    data: Annotated[UserLoginRequest, Form()],
    use_case: FromDishka[LoginUserInteractor],
):
    user_id = await use_case(login_data=UserLoginData(login=data.login, password=data.password))
    access_token = idp.create_access_token(user_id=user_id)
    refresh_token = await idp.create_refresh_token(user_id=user_id)

    response = JSONResponse(content={"username": data.login, "access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
        max_age=idp.settings.refresh_token_lifetime_s,
    )
    return response


@router.post("/auth/sign-out")
@inject
async def logout_user_api(idp: FromDishka[IdentityProvider], response: Response, refresh_token: str = Cookie):
    await idp.delete_refresh_token(token=refresh_token)
    response.delete_cookie(
        key="refresh_token",
        path="/auth/refresh",
    )


@router.post("/auth/refresh")
@inject
async def refresh(idp: FromDishka[IdentityProvider], response: Response, refresh_token: str = Cookie):
    new_refresh_token, user_id = await idp.rotate_refresh_token(token=refresh_token)
    access_token = idp.create_access_token(user_id=user_id)
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
        max_age=idp.settings.refresh_token_lifetime_s,
    )
    return response


@router.get("/main")
@inject
async def main_test(
    idp: FromDishka[IdentityProvider], credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    result = idp.validate_access_token(token=credentials.credentials)
    return f"HELLO {result} !"


# ratm1r
# RtmTest26!
