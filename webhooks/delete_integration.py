import httpx
from fastapi import Response
from loguru import logger
from port_ocean.clients.port.types import RequestOptions
from port_ocean.context.ocean import ocean
from port_ocean.core.models import Entity
from pydantic import BaseModel

from clients import (
    initialize_action_client,
    initialize_entity_client,
    initialize_integration_client,
)
from webhooks._types import PortContext


class DeleteIntegrationRequest(BaseModel):
    integration: str
    port_context: PortContext


class DeleteIntegrationResponse(BaseModel):
    ok: bool
    status_code: int


@ocean.router.post("/delete")
async def delete_integration(
    data: DeleteIntegrationRequest, response: Response
) -> DeleteIntegrationResponse:
    """
    We're implementing this here so we can update the action run state
    """
    action = initialize_action_client(data.port_context.run_id)

    await action.log(f"Starting action to delete integration {data.integration}")

    client = initialize_integration_client()
    entity_client = initialize_entity_client()
    is_deleted = False
    status_code = 0

    entity = Entity(
        identifier=data.integration,
        blueprint=data.port_context.blueprint,
        # the rest of the values below are useless to the request
        # and are only added for typing compliance
        title="needless title",
    )
    request_options: RequestOptions = {
        "delete_dependent_entities": False,
        # the rest of the values below are useless to the request
        # and are only added for typing compliance
        "create_missing_related_entities": False,
        "merge": False,
        "validation_only": False,
    }

    try:
        await action.log(f"Triggering integration deletion for {data.integration}")
        is_deleted = await client.delete_integration(data.integration)
        await action.log("Integration deleted successfully! 😎")
        await action.log("Deleting integration entity from catalog")
        await entity_client.delete_entity(entity, request_options)
        await action.log_final("Integration entity deleted from catalog ✅")
        status_code = 200
    except httpx.HTTPStatusError as e:
        response.status_code = e.response.status_code
        status_code = e.response.status_code
        await action.log_failure("Integration failed to delete due to wrong config 🥺")
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed: {e}")
        await action.log_failure(
            "Integration deletion failed due to unknown reasons 😭"
        )
        raise e

    return DeleteIntegrationResponse(ok=is_deleted, status_code=status_code)
