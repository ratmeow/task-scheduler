from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Cookie, Depends, Form, Query, Response
from starlette.responses import JSONResponse

from task_scheduler.application.dto import (
    TaskCreateData,
    TaskListFilter,
    TaskListNavigation,
    TaskUpdateData,
    UserLoginData,
    UserRegisterData,
)
from task_scheduler.application.interactors import (
    CreateTaskInteractor,
    DeleteTaskInteractor,
    ListTaskInteractor,
    LoginUserInteractor,
    RegisterUserInteractor,
    UpdateTaskInteractor,
)
from task_scheduler.infrastructure.idp.provider import IdentityProvider

from ..infrastructure.interfaces import EmailPublisher
from .cookie_manager import TokenCookieManager
from .exceptions import UnauthorizedError
from .schemas import (
    TaskCreateRequest,
    TaskFiltersRequest,
    TaskResponse,
    TaskUpdateRequest,
    UserLoginRequest,
    UserRegisterRequest,
)

router = APIRouter(prefix="/api")


def get_access_token(
    access_token: Annotated[str | None, Cookie()] = None,
) -> str:
    if access_token is None:
        raise UnauthorizedError()
    return access_token


AccessToken = Annotated[str, Depends(get_access_token)]


@router.post("/auth/sign-up")
@inject
async def register_user(
    data: Annotated[UserRegisterRequest, Form()],
    use_case: FromDishka[RegisterUserInteractor],
    email_publisher: FromDishka[EmailPublisher],
):
    user = await use_case(register_data=UserRegisterData(email=data.email, login=data.login, password=data.password))
    await email_publisher.publish(email=user.email, text=f"Welcome to task scheduler dear {user.login}")
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
async def main_test(idp: FromDishka[IdentityProvider], access_token: AccessToken):
    result = idp.validate_access_token(token=access_token)
    return f"HELLO {result} !"


@router.post("/task", response_model=TaskResponse)
@inject
async def task_create(
    data: TaskCreateRequest,
    use_case: FromDishka[CreateTaskInteractor],
    idp: FromDishka[IdentityProvider],
    access_token: AccessToken,
) -> TaskResponse:
    user_id = idp.validate_access_token(token=access_token)
    task = await use_case(
        task_data=TaskCreateData(user_id=user_id, name=data.name, description=data.description, due_ts=data.due_ts)
    )
    response = TaskResponse.from_domain_model(data=task)
    return response


@router.patch("/task/{task_id}", response_model=TaskResponse)
@inject
async def task_update(
    task_id: str,
    data: TaskUpdateRequest,
    use_case: FromDishka[UpdateTaskInteractor],
    idp: FromDishka[IdentityProvider],
    access_token: AccessToken,
) -> TaskResponse:
    idp.validate_access_token(token=access_token)
    task = await use_case(
        task_data=TaskUpdateData(
            task_id=task_id,
            name=data.name,
            description=data.description,
            due_ts=data.due_ts,
            is_complete=data.is_complete,
        )
    )
    response = TaskResponse.from_domain_model(data=task)
    return response


@router.delete("/task/{task_id}", status_code=200)
@inject
async def task_delete(
    task_id: str,
    use_case: FromDishka[DeleteTaskInteractor],
    idp: FromDishka[IdentityProvider],
    access_token: AccessToken,
) -> None:
    idp.validate_access_token(token=access_token)
    await use_case(task_id=task_id)


@router.get("/tasks")
@inject
async def tasks_get(
    use_case: FromDishka[ListTaskInteractor],
    idp: FromDishka[IdentityProvider],
    access_token: AccessToken,
    filters: Annotated[TaskFiltersRequest, Query()],
) -> list[TaskResponse]:
    user_id = idp.validate_access_token(token=access_token)
    tasks = await use_case(
        filters=TaskListFilter(user_id=user_id, name=filters.name, is_complete=filters.is_complete),
        navigation=TaskListNavigation(
            sort_by=filters.sort_by, sort_desc=filters.sort_desc, limit=filters.limit, offset=filters.offset
        ),
    )
    response = [TaskResponse.from_domain_model(data=task) for task in tasks]
    return response


# ratm1r
# RtmTest26!
