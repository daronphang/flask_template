class CustomException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code

        Exception.__init__(self)


class HttpError(CustomException):
    pass


class DatabaseError(CustomException):
    pass


class MissingSchema(CustomException):
    pass


class InvalidField(CustomException):
    pass


class MissingKey(CustomException):
    pass


class CeleryFailure(Exception):
    pass