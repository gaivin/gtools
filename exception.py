class BaseException(Exception):
    type = "BASE_ERROR"


class RequestDataError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_DATA_ERROR"


class RequestDataFormatError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_DATA_FORMAT_ERROR"


class RequestMethodError(BaseException):
    def __init__(self, message):
        self.message = message
        self.type = "REQUEST_METHOD_ERROR"
