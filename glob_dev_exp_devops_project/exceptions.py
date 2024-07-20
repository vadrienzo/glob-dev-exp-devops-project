from enum import Enum


class DBFailureReasonsEnum(str, Enum):
    ID_ALREADY_EXISTS = "id already exists"
    NO_SUCH_ID = "no such id"


class ServerFailureReasonsEnum(str, Enum):
    INTERNAL_SERVER_ERROR = "internal server error"
    INVALID_REQUEST = "invalid request"


class NoDataFoundDBException(ValueError):
    pass
