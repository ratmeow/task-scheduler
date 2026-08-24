from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from task_scheduler.config import Config
from task_scheduler.ioc import AppProvider
from task_scheduler.presentation.handlers import router


def create_app():
    config = Config()

    app = FastAPI()
    app.include_router(router)

    container = make_async_container(AppProvider(), context={Config: config})
    setup_dishka(container=container, app=app)
    return app
