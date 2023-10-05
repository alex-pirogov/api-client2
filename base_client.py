import json
import logging
from abc import ABC
from logging import Logger
from typing import Any, Dict, Optional, Type

from aiohttp import ClientResponse, ClientSession
from pydantic import TypeAdapter

from .request_config import RequestConfig, ReturnType


class BaseApiClientError(Exception):
    def __init__(self, config: RequestConfig[Any], status: int, text: str) -> None:
        self.request = config
        self.status = status
        self.text = text
        super().__init__()
    
    def __str__(self) -> str:
        return f"[{self.status}] {self.text if self.text else '*no content*'}"


class BaseApiClient(ABC):
    api_client_error_class: Type[BaseApiClientError] = BaseApiClientError

    def __init__(
            self,
            base_url: str,
            logger: Logger,
            headers: Optional[Dict[str, str]] = None
    ) -> None:
        self.base_url = base_url
        self.logger = logger
        self.headers = headers or {}

    def get_url(self, url: str) -> str:
        print(self.base_url + url)
        return self.base_url + url

    async def check_response(
            self,
            response: ClientResponse,
            config: RequestConfig[Any]
    ) -> None:
        status, text = response.status, await response.text()
        
        if status < 400:
            return
        
        if status not in config.allowed_error_codes:
            await self.log_request(response, config, logging.ERROR)
            raise self.api_client_error_class(config, status, text)
            
    def parse_response(self, response_json: Any, config: RequestConfig[ReturnType]) -> ReturnType:
        if type(config.return_type) is None:
            return config.return_type()
        
        return TypeAdapter(config.return_type).validate_python(response_json)

    async def log_request(
            self,
            response: ClientResponse,
            config: RequestConfig[Any],
            level: int = logging.DEBUG
    ) -> None:
        if not self.logger:
            return
        
        status, content = response.status, await response.text()

        text = f"[{config.method}] -> {status}\nURL: {config.url}\n"
        if config.payload:
            text += f"PAYLOAD:\n{json.dumps(config.payload, ensure_ascii=False, indent=2)}\n"
        
        text += f"RESP:\n{content if content else '*no content*'}"
        self.logger.log(level, text)

    async def make_request(self, config: RequestConfig[ReturnType]) -> ReturnType:
        async with ClientSession(
                headers=self.headers
        ) as session:
            async with session.request(
                    method=config.method,
                    url=self.get_url(config.url),
                    json=config.payload
            ) as response:
                await response.read()
                await self.check_response(response, config)
                await self.log_request(response, config)
                return self.parse_response(await response.json(), config)
            