from typing import Literal

from port_ocean.clients.port.authentication import PortAuthentication

from clients._mixin import ClientMixin

type LogTerminationStatus = Literal["SUCCESS", "FAILURE"]


class ActionClient(ClientMixin):
    def __init__(
        self,
        port_client_auth: PortAuthentication,
        run_id: str,
        base_url: str = "https://api.port.io",
    ):
        """
        Initialize the integration client.

        Args:
            port_client_auth: Port authentication object
            base_url: The base URL for the Port API (defaults to https://api.port.io)
        """
        super().__init__()
        self.run_id = run_id
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

    async def _send_log_message(
        self,
        message: str,
        final: bool = False,
        final_label: str = "Completed successfully!",
        termination_status: LogTerminationStatus = "SUCCESS",
    ):
        url = f"{self.base_url}/v1/actions/runs/{self.run_id}/logs"

        json = {"message": message}

        if final:
            json["statusLabel"] = final_label
            json["terminationStatus"] = termination_status

        await self._send_request("POST", url, json=json)

    async def log(self, message: str):
        return await self._send_log_message(message)

    async def log_final(self, message: str):
        return await self._send_log_message(message, final=True)

    async def log_failure(self, message: str):
        return await self._send_log_message(
            message,
            final=True,
            final_label="Failed woefully!",
            termination_status="FAILURE",
        )
