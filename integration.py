from enum import StrEnum
from typing import Literal

from port_ocean.core.handlers.port_app_config.api import APIPortAppConfig
from port_ocean.core.handlers.port_app_config.models import (
    PortAppConfig,
    ResourceConfig,
    Selector,
)
from port_ocean.core.integrations.base import BaseIntegration
from pydantic.fields import Field

class ObjectKind(StrEnum):
    INTEGRATION = "integration"

class IntegrationSelector(Selector):
    log_limit: int = Field(
        alias="logLimit",
        default=300,
        description="The maximum number of logs to fetch from an integration to determine its health. Cannot be greater than 300",
    )

    @classmethod
    def validate_log_limit(cls, v: int) -> int:
        if v > 300:
            raise ValueError("log_limit cannot be greater than 300")
        return v

class IntegrationResourceConfig(ResourceConfig):
    selector: IntegrationSelector
    kind: Literal["integration"]


class IntegrationAppConfig(PortAppConfig):
    resources: list[IntegrationResourceConfig | ResourceConfig] = Field(
        default_factory=list,
    )


class IntegrationIntegration(BaseIntegration):
    class AppConfigHandlerClass(APIPortAppConfig):
        CONFIG_CLASS = IntegrationAppConfig
