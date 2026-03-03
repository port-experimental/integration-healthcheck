import asyncio
from itertools import batched
from typing import Any

from port_ocean.clients.port.authentication import PortAuthentication

from clients._mixin import ClientMixin


class BlueprintClient(ClientMixin):
    def __init__(
        self,
        port_client_auth: PortAuthentication,
        base_url: str = "https://api.port.io",
    ):
        """
        Initialize the integration client.

        Args:
            port_client_auth: Port authentication object
            base_url: The base URL for the Port API (defaults to https://api.port.io)
        """
        super().__init__()
        self.base_url = base_url
        self.auth = port_client_auth

    async def _get_headers(self) -> dict[str, str]:
        """
        Get the headers required for API requests, including the authentication token.

        Returns:
            Dictionary containing Authorization and Content-Type headers
        """
        token = await self.auth.token

        return {
            "Authorization": token,
            "Content-Type": "application/json",
        }

    async def _get_blueprint_entity_count(self, blueprint: str) -> int:
        response: dict[str, int] = await self._send_request(
            "GET", f"{self.base_url}/v1/blueprints/{blueprint}/entities-count"
        )

        return response["count"]

    async def _get_blueprints(self) -> list[dict[str, Any]]:
        response: dict[str, list[dict[str, Any]]] = await self._send_request(
            "GET", f"{self.base_url}/v1/blueprints"
        )

        return response["blueprints"]

    async def get_blueprints(
        self, get_entity_count: bool = False
    ) -> list[dict[str, Any]]:
        blueprints = await self._get_blueprints()
        batched_blueprints = batched(blueprints, self.MAX_CHUNK_REQUEST_SIZE)
        

        if get_entity_count:
            for batch in batched_blueprints:
                tasks = [
                    self._get_blueprint_entity_count(blueprint["identifier"])
                    for blueprint in batch
                ]
    
                results = zip((await asyncio.gather(*tasks)), blueprints)
                for count, blueprint in results:
                    blueprint["__entityCount"] = count

        return blueprints
