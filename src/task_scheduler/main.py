from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from task_scheduler.config import Config
from task_scheduler.ioc import AppProvider
from task_scheduler.presentation.exceptions import register_exception_handlers
from task_scheduler.presentation.handlers import router


def create_app():
    config = Config()

    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app=app)

    container = make_async_container(AppProvider(), context={Config: config})
    setup_dishka(container=container, app=app)
    return app
