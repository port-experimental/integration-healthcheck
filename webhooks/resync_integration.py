import httpx
from fastapi import Response
from loguru import logger
from port_ocean.context.ocean import ocean
from pydantic import BaseModel

from clients import initialize_action_client, initialize_integration_client
from webhooks._types import PortContext


class ResyncIntegrationRequest(BaseModel):
    integration: str
    port_context: PortContext


class ResyncIntegrationResponse(BaseModel):
    ok: bool
    status_code: int


@ocean.router.post("/resync")
async def resync_integration(
    data: ResyncIntegrationRequest, response: Response
) -> ResyncIntegrationResponse:
    """
    We're implementing this here so we can update the action run state
    """
    action = initialize_action_client(data.port_context.run_id)

    await action.log(f"Starting integration resync for {data.integration}")

    client = initialize_integration_client()
    is_resynced = False
    status_code = 0

    try:
        await action.log(f"Triggering integration resync for {data.integration}")
        is_resynced = await client.resync_integration(data.integration)
        await action.log_final("Integration resync triggered successfully! 😎")
        status_code = 200
    except httpx.HTTPStatusError as e:
        response.status_code = e.response.status_code
        status_code = e.response.status_code
        await action.log_failure(
            f"Integration resync failed to trigger: {e.response.json().get("message")} 🥺"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP request failed: {e}")
        await action.log_failure(
            "Integration resync failed to trigger for unknown reasons 😭"
        )
        raise e

    return ResyncIntegrationResponse(ok=is_resynced, status_code=status_code)
