from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Form, Response
from starlette.responses import JSONResponse

from task_scheduler.application.dto import UserRegisterData
from task_scheduler.application.interactors import (
    LoginUserInteractor,
    RegisterUserInteractor,
)

from .schemas import UserRegisterRequest

router = APIRouter(prefix="/api")


@router.post("/auth/sign-up")
@inject
async def register_user(data: Annotated[UserRegisterRequest, Form()], use_case: FromDishka[RegisterUserInteractor]):
    await use_case(register_data=UserRegisterData(login=data.login, password=data.password))
    return Response(status_code=200)


@router.post("/auth/sign-in")
@inject
async def login_user_api(data: Annotated[UserRegisterRequest, Form()], use_case: FromDishka[LoginUserInteractor]):
    await use_case(login_data=UserRegisterData(login=data.login, password=data.password))
    response = JSONResponse(content={"username": data.login})
    return response


@router.post("/auth/sign-out")
@inject
async def logout_user_api():
    pass
