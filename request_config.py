from abc import ABC
from enum import Enum
from typing import Generic, List, Optional, Type, TypeAlias, TypeVar, Union

JSON: TypeAlias = Union[dict[str, 'JSON'], list['JSON'], str, int, float, bool, None]
ReturnType = TypeVar('ReturnType')


class HttpMethod(str, Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    PATCH = 'patch'
    DELETE = 'delete'


class GenericRequestConfig(ABC, Generic[ReturnType]):
    def __init__(
            self,
            method: HttpMethod,
            url: str,
            return_type: Type[ReturnType] = type(None),
            payload: Optional[JSON] = None,
            allowed_error_codes: Optional[List[int]] = None,
            **query_args: str
    ) -> None:
        self.method = method
        self.url = url
        self.payload = payload
        self.return_type = return_type
        self.allowed_error_codes = allowed_error_codes or []
        self.query_args = query_args


class RequestConfig(GenericRequestConfig[ReturnType]):
    pass
