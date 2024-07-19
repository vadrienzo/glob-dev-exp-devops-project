from enum import Enum


class DBFailureReasonsEnum(str, Enum):
    ID_ALREADY_EXISTS = "id already exists"
    NO_SUCH_ID = "no such id"


class NoDataFoundDBException(ValueError):
    pass
