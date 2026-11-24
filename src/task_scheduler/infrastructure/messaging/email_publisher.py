from celery import Celery
from starlette.concurrency import run_in_threadpool


class CeleryEmailPublisher:
    def __init__(self, celery: Celery):
        self._celery = celery

    async def publish(self, email: str, text: str) -> str:
        result = await run_in_threadpool(
            self._celery.send_task,
            "email.send",
            kwargs={
                "email": email,
                "text": text,
            },
        )

        return result.id
