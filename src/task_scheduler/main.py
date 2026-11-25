from celery import Celery
from dishka import make_async_container, make_container
from dishka.integrations.celery import setup_dishka as celery_dishka
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from task_scheduler.config import Config
from task_scheduler.ioc import AppProvider, WorkerProvider
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


def create_worker() -> None:
    config = Config()

    celery = Celery(
        main="app",
        broker=config.rabbitmq.amqp_url,
    )
    celery.conf.imports = ("task_scheduler.presentation.tasks",)
    container = make_container(WorkerProvider(), context={Config: config})
    celery_dishka(container=container, app=celery)
    try:
        celery.worker_main(
            [
                "worker",
                "--loglevel=INFO",
            ]
        )
    finally:
        container.close()
