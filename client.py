"""
Integration client for interacting with Port's API.
This module provides functionality to manage and monitor integrations, including health checks and log retrieval.
"""

import asyncio
from typing import Any, Literal

import httpx
from loguru import logger
from port_ocean.clients.port.authentication import PortAuthentication
from port_ocean.utils import http_async_client

# Define possible integration health states
type IntegrationHealth = Literal["HEALTHY", "WARNING", "ERROR", "INACTIVE"]


class IntegrationClient:
    """
    Client for interacting with Port's integration API.
    
    This client handles authentication, making requests to Port's API, and processing integration-related data.
    It provides methods to fetch integration details, logs, and perform health checks.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        port_client_auth: PortAuthentication,
        base_url: str = "https://api.port.io",
    ):
        """
        Initialize the integration client.
        
        Args:
            client_id: The client ID for authentication
            client_secret: The client secret for authentication
            port_client_auth: Port authentication object
            base_url: The base URL for the Port API (defaults to https://api.port.io)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.client = http_async_client
        self.auth = port_client_auth

    async def _get_headers(self) -> dict[str, Any]:
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

    async def _send_request[T](self, method: str, url: str, **kwargs: Any) -> T:
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
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Request failed with status code {e.response.status_code}: {e.response.text}"
            )
            raise e
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise e

    async def _fetch_integrations(self) -> list[dict[str, Any]]:
        """
        Fetch all integrations from the Port API.
        
        Returns:
            List of integration dictionaries containing integration details
        """
        logger.info(f"Fetching integrations from {self.base_url}")
        integrations: dict[str, Any | list[dict[str, Any]]] = await self._send_request(
            "GET", f"{self.base_url}/v1/integration"
        )
        return integrations["integrations"]

    async def _get_integration_logs(
        self, integration_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Fetch logs for a specific integration.
        
        Args:
            integration_id: The ID of the integration to fetch logs for
            limit: Maximum number of logs to return (default: 100)
            
        Returns:
            List of log entries for the integration
        """
        logger.info(
            f"Fetching logs for integration {integration_id} with limit {limit}"
        )
        logs: dict[str, Any | list[dict[str, Any]]] = await self._send_request(
            "GET",
            f"{self.base_url}/v1/integration/{integration_id}/logs",
            params={"limit": limit},
        )
        logs_list = logs["data"]
        logger.info(f"Fetched {len(logs_list)} logs")
        return logs_list

    async def _get_integration_audit_logs(
        self, integration_id: str, from_date: str
    ) -> list[dict[str, Any]]:
        """
        Fetch audit logs for a specific integration from a given date.
        
        Args:
            integration_id: The ID of the integration to fetch audit logs for
            from_date: The date to fetch logs from
            
        Returns:
            List of audit log entries for the integration
        """
        logger.info(
            f"Fetching audit logs for integration {integration_id} with from date {from_date}"
        )
        logs: dict[str, Any | list[dict[str, Any]]] = await self._send_request(
            "GET",
            f"{self.base_url}/v1/audit-log",
            params={
                "from": from_date,
                "InstallationId": integration_id,
                "limit": 1000,
                "includes": ["status", "message"],
            },
        )
        audits = logs["audits"]
        logger.info(f"Fetched {len(audits)} audit logs")
        return audits

    def _determine_integration_health_from_logs(
        self, logs: list[dict[str, Any]], from_date: str
    ) -> tuple[IntegrationHealth, str]:
        """
        Determine the health status of an integration based on its logs.
        
        Args:
            logs: List of log entries to analyze
            from_date: The date to consider logs from
            
        Returns:
            Tuple containing the health status and any error message
        """
        if not logs:
            return "INACTIVE", ""
        for log in reversed(logs):
            if log["level"] == "ERROR":
                return "ERROR", log["message"]
            if log["level"] == "WARNING":
                return "WARNING", log["message"]
            if log["timestamp"] < from_date:
                return "HEALTHY", ""
        return "HEALTHY", ""

    def _determine_integration_health_from_audit_logs(
        self, logs: list[dict[str, Any]]
    ) -> tuple[IntegrationHealth, str]:
        """
        Determine the health status of an integration based on its audit logs.
        
        Args:
            logs: List of audit log entries to analyze
            
        Returns:
            Tuple containing the health status and any error message
        """
        if not logs:
            return "INACTIVE", ""
        for log in logs:
            if log["status"] == "FAILURE":
                return "ERROR", log["message"]
        return "HEALTHY", ""

    async def _enrich_integration_health(
        self, integration: dict[str, Any], log_limit: int
    ) -> dict[str, Any]:
        """
        Enrich an integration object with health status information.
        
        This method checks both audit logs and regular logs to determine the integration's health.
        The health status is added as '__health' and any error message as '__errorMessage' to the integration dict.
        
        Args:
            integration: The integration dictionary to enrich
            log_limit: Maximum number of logs to fetch
            
        Returns:
            The enriched integration dictionary
        """
        logger.info(
            f"Enriching integration health for integration: {integration['_id']}"
        )
        if "resyncState" not in integration:
            integration["__health"] = "INACTIVE"
            integration["__errorMessage"] = ""
            return integration

        # First check audit logs for failures
        logs = await self._get_integration_audit_logs(
            integration["installationId"],
            (
                integration["resyncState"].get("lastResyncStart")
                or integration["createdAt"]
            ),
        )
        health, error_message = self._determine_integration_health_from_audit_logs(
            logs,
        )
        if health != "HEALTHY":
            integration["__health"] = health
            integration["__errorMessage"] = error_message
            return integration

        # If audit logs show healthy, check regular logs for warnings or errors
        logs = await self._get_integration_logs(
            integration["installationId"], log_limit
        )
        health, error_message = self._determine_integration_health_from_logs(
            logs,
            integration["resyncState"].get("lastResyncStart")
            or integration["createdAt"],
        )
        integration["__health"] = health
        integration["__errorMessage"] = error_message
        return integration

    async def get_integrations(self, log_limit: int) -> list[dict[str, Any]]:
        """
        Get all integrations with their health status.
        
        Args:
            log_limit: Maximum number of logs to fetch for each integration
            
        Returns:
            List of integration dictionaries enriched with health information
        """
        integrations = await self._fetch_integrations()
        tasks = [
            self._enrich_integration_health(integration, log_limit)
            for integration in integrations
        ]
        integrations = await asyncio.gather(*tasks)
        return integrations

    async def healthcheck(self) -> bool:
        """
        Perform a health check of the connection to Port's API.
        
        Returns:
            True if the connection is healthy, False otherwise
        """
        response: dict[str, Any] = await self._send_request(
            "GET", f"{self.base_url}/v1/organization"
        )
        return bool(response["ok"])
