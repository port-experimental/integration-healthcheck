import asyncio
import httpx
from loguru import logger
from port_ocean.utils import http_async_client
from port_ocean.clients.port.authentication import PortAuthentication
from typing import Any, Literal

type IntegrationHealth = Literal["HEALTHY", "WARNING", "ERROR", "INACTIVE"]

class IntegrationClient:
    def __init__(self, client_id: str, client_secret: str, port_client_auth: PortAuthentication, base_url: str = "https://api.port.io"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.client = http_async_client
        self.auth = port_client_auth
    
    async def _get_headers(self) -> dict[str, Any]:
        token = await self.auth.token

        return {
            "Authorization": token,
            "Content-Type": "application/json",
        }
    
    async def _send_request[T](self, method: str, url: str, **kwargs: Any) -> T:
        logger.info(f"Sending request to {url} with method {method}")
        try:
            response = await self.client.request(
                method,
                url,
                headers=await self._get_headers(),
                **kwargs
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Request failed with status code {e.response.status_code}: {e.response.text}")
            raise e
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise e

    async def _fetch_integrations(self) -> list[dict[str, Any]]:
        logger.info(f"Fetching integrations from {self.base_url}")
        integrations: dict[str, Any | list[dict[str, Any]]] = await self._send_request("GET", f"{self.base_url}/v1/integration")
        return integrations["integrations"]
    
    async def _get_integration_logs(self, integration_id: str, limit: int = 100) -> list[dict[str, Any]]:
        logger.info(f"Fetching logs for integration {integration_id} with limit {limit}")
        logs: dict[str, Any | list[dict[str, Any]]] = await self._send_request(
            "GET",
            f"{self.base_url}/v1/integration/{integration_id}/logs",
            params={"limit": limit}
        )
        logs_list = logs["data"]
        logger.info(f"Fetched {len(logs_list)} logs")
        return logs_list
    
    async def _get_integration_audit_logs(self, integration_id: str, from_date: str) -> list[dict[str, Any]]:
        logger.info(f"Fetching audit logs for integration {integration_id} with from date {from_date}")
        logs: dict[str, Any | list[dict[str, Any]]] = await self._send_request(
            "GET",
            f"{self.base_url}/v1/audit-log",
            params={
                "from": from_date,
                "InstallationId": integration_id,
                "limit": 1000,
                "includes": ["status", "message"]
            }
        )
        audits = logs["audits"]
        logger.info(f"Fetched {len(audits)} audit logs")
        return audits
    
    def _determine_integration_health_from_logs(self, logs: list[dict[str, Any]]) -> tuple[IntegrationHealth, str]:
        logger.info(f"Determining integration health from logs: {logs}")
        for log in reversed(logs):
            if log["level"] == "ERROR":
                return "ERROR", log["message"]
            if log["level"] == "WARNING":
                return "WARNING", log["message"]
        return "HEALTHY", ""
    
    def _determine_integration_health_from_audit_logs(self, logs: list[dict[str, Any]]) -> tuple[IntegrationHealth, str]:
        logger.info(f"Determining integration health from audit logs: {logs}")
        for log in logs:
            if log["status"] == "FAILURE":
                return "ERROR", log["message"]
        return "HEALTHY", ""
    
    async def _enrich_integration_health(self, integration: dict[str, Any], log_limit: int) -> dict[str, Any]:
        logger.info(f"Enriching integration health for integration: {integration['id']}")
        if "resyncState" not in integration:
            integration["__health"] = "INACTIVE"
            integration["__errorMessage"] = ""
        logs = await self._get_integration_audit_logs(
            integration["id"],
            (integration["resyncState"].get("lastResyncStart") or integration["createdAt"])
        )
        health, error_message = self._determine_integration_health_from_audit_logs(logs)
        if health != "HEALTHY":
            integration["__health"] = health
            integration["__errorMessage"] = error_message
            return integration
        
        logs = await self._get_integration_logs(integration["id"], log_limit)
        health, error_message = self._determine_integration_health_from_logs(logs)
        integration["__health"] = health
        integration["__errorMessage"] = error_message
        return integration

    async def get_integrations(self, log_limit: int) -> list[dict[str, Any]]:
        integrations = await self._fetch_integrations()
        tasks = [self._enrich_integration_health(integration, log_limit) for integration in integrations]
        integrations = await asyncio.gather(*tasks)
        return integrations

    async def healthcheck(self) -> bool:
        response: dict[str, Any] = await self._send_request("GET", f"{self.base_url}/v1/organization")
        return bool(response["ok"])
