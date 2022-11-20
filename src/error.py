class AimharderError(Exception):

    def __init__(self, error_message=None):
        self.error_message = error_message


class TooManyAttemptsError(AimharderError):
    pass


class UnknownError(AimharderError):
    pass


class AimharderResponseError(AimharderError):

    def __init__(self, action: str, book_state: int, error_message=None, error_response=None):
        super().__init__(error_message)
        self.action = action
        self.book_state = book_state
        self.error_response = error_response
