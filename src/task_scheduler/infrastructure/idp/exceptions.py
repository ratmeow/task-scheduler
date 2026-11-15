from task_scheduler.application.exceptions import ApplicationError


class ExpiredTokenError(ApplicationError):
    def __init__(self, token_type: str):
        super().__init__(message=f"{token_type} token has expired!")


class WrongTokenError(ApplicationError):
    def __init__(self, token_type: str):
        super().__init__(message=f"Wrong {token_type} token!")
