from port_ocean.clients.port.mixins.entities import EntityClientMixin
from port_ocean.context.ocean import ocean
from port_ocean.utils import http_async_client

from .action import ActionClient
from .integration import IntegrationClient
from .slack import SlackClient


def initialize_integration_client() -> IntegrationClient:
    return IntegrationClient(
        ocean.port_client.auth,
        ocean.config.port.base_url,
    )


def initialize_action_client(run_id: str) -> ActionClient:
    return ActionClient(
        ocean.port_client.auth,
        run_id,
        ocean.config.port.base_url,
    )


def initialize_entity_client() -> EntityClientMixin:
    return EntityClientMixin(ocean.port_client.auth, http_async_client)


__all__ = [
    "IntegrationClient",
    "SlackClient",
    "initialize_integration_client",
    "initialize_action_client",
]
