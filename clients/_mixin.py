"""
Base client mixin for interacting with third-party APIs.
"""

from abc import ABC, abstractmethod
from typing import Any, cast

import httpx
from loguru import logger
from port_ocean.utils import http_async_client


class ClientMixin(ABC):
    """
    Client for interacting with different APIs.

    This client provides methods to send requests and other utility methods.
    """
    
    MAX_CHUNK_REQUEST_SIZE: int = 20

    def __init__(self):
        self.client = http_async_client

    @abstractmethod
    async def _get_headers(self) -> dict[str, Any]:
        """
        Get the headers required for API requests, including the authentication token.

        Returns:
            Dictionary containing dynamic headers
        """
        ...

    async def _send_request[T](self, method: str, url: str, **kwargs: Any) -> T:  # type: ignore
        """
        Send an HTTP request to the Port API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: The endpoint URL
            **kwargs: Additional arguments to pass to the request

        Returns:
            The JSON response from the API

        Raises:
            httpx.HTTPStatusError: If the request fails with a non-200 status code
            httpx.HTTPError: If there's a general HTTP error
        """
        logger.info(f"Sending request to {url} with method {method}")
        try:
            response = await self.client.request(
                method, url, headers=await self._get_headers(), **kwargs
            )
            return cast(T, response.json())
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Request failed with status code {e.response.status_code}: {e.response.text}"
            )
            raise e
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise e
