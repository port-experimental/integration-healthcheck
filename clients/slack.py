from dataclasses import dataclass
from typing import Any
from clients._mixin import ClientMixin


@dataclass
class SlackMessage:
    text: str
    attachments: dict[str, Any]

class SlackClient(ClientMixin):
    def __init__(self):
        super().__init__()
    
    async def send_webhook_message(self, webhook_url: str, message):
        response = await self._send_request(
            "POST",
            webhook_url
        )