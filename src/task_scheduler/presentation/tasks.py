from celery import shared_task
from dishka.integrations.celery import DishkaTask, FromDishka

from task_scheduler.infrastructure.interfaces import EmailSender


@shared_task(name="email.send", base=DishkaTask)
def send_email(email: str, text: str, email_sender: FromDishka[EmailSender]) -> None:
    email_sender.send(email=email, text=text)
