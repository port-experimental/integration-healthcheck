from typing import Any, cast

from loguru import logger
from port_ocean.context.event import event
from port_ocean.context.ocean import ocean

from client import IntegrationClient
from integration import IntegrationResourceConfig, ObjectKind


def initialize_client() -> IntegrationClient:
    return IntegrationClient(
        ocean.config.port.client_id,
        ocean.config.port.client_secret,
        ocean.port_client.auth,
        ocean.config.port.base_url,
    )


@ocean.on_resync(ObjectKind.INTEGRATION)
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    selector = cast(IntegrationResourceConfig, event.resource_config).selector
    selector.validate_log_limit(selector.log_limit)
    logger.info(f"Resyncing integrations with log limit: {selector.log_limit}")
    client = initialize_client()
    integrations = await client.get_integrations(log_limit=selector.log_limit)
    logger.info(f"Received batch of {len(integrations)} integrations")
    return integrations


@ocean.on_start()
async def on_start() -> None:
    logger.info("Starting Port integration")
    client = initialize_client()

    status = await client.healthcheck()
    if not status:
        logger.error("Port integration is not healthy")
        raise Exception("Port integration is not healthy")

    logger.info("Port integration is healthy")
