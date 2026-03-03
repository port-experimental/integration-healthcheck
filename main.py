from typing import Any, cast

from loguru import logger
from port_ocean.context.event import event
from port_ocean.context.ocean import ocean

from clients import initialize_blueprint_client, initialize_integration_client
from integration import BlueprintResourceConfig, IntegrationResourceConfig, ObjectKind


@ocean.on_resync(ObjectKind.INTEGRATION)
async def on_resync_integration(kind: str) -> list[dict[Any, Any]]:
    selector = cast(IntegrationResourceConfig, event.resource_config).selector
    selector.validate_log_limit(selector.log_limit)
    logger.info(
        f"Resyncing integrations with log limit: {selector.log_limit} and context logs count: {selector.context_logs_count}"
    )
    client = initialize_integration_client()
    integrations = await client.get_integrations(
        log_limit=selector.log_limit, context_logs_count=selector.context_logs_count
    )
    logger.info(f"Received batch of {len(integrations)} integrations")
    return integrations


@ocean.on_resync(ObjectKind.BLUEPRINT)
async def on_resync_blueprint(kind: str) -> list[dict[Any, Any]]:
    selector = cast(BlueprintResourceConfig, event.resource_config).selector
    client = initialize_blueprint_client()
    blueprints = await client.get_blueprints(get_entity_count=selector.get_entity_count)
    logger.info(f"Received batch of {len(blueprints)} blueprints")
    return blueprints


@ocean.on_resync(ObjectKind.RESYNC_EVENT)
async def on_resync_resync_event(kind: str) -> list[dict[Any, Any]]:
    client = initialize_integration_client()
    resync_events = await client.get_resync_events()
    logger.info(f"Received batch of {len(resync_events)} resync events")
    return resync_events


@ocean.on_start()
async def on_start() -> None:
    logger.info("Starting Port integration")
    client = initialize_integration_client()

    status = await client.healthcheck()
    if not status:
        logger.error("Port integration is not healthy")
        raise Exception("Port integration is not healthy")

    logger.info("Port integration is healthy")
