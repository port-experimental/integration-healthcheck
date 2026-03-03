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
    BLUEPRINT = "blueprint"
    RESYNC_EVENT = "resync-event"


class IntegrationSelector(Selector):
    log_limit: int = Field(
        alias="logLimit",
        default=300,
        description="The maximum number of logs to fetch from an integration to determine its health. Cannot be greater than 300",
    )
    context_logs_count: int = Field(
        alias="contextLogsCount",
        default=4,
        description="The number of recent logs to include in error/warning messages for context",
    )

    @classmethod
    def validate_log_limit(cls, v: int) -> int:
        if v > 300:
            raise ValueError("log_limit cannot be greater than 300")
        return v


class IntegrationResourceConfig(ResourceConfig):
    selector: IntegrationSelector   # type: ignore
    kind: Literal["integration"]    # type: ignore


class BlueprintSelector(Selector):
    get_entity_count: bool = Field(
        alias="getEntityCount",
        default=False,
        description="Get the number of entities existing for this blueprint"
    )


class BlueprintResourceConfig(ResourceConfig):
    selector: BlueprintSelector # type: ignore
    kind: Literal["blueprint"]  # type: ignore


class IntegrationAppConfig(PortAppConfig):
    resources: list[
        IntegrationResourceConfig
        | BlueprintResourceConfig
        | ResourceConfig
    ] = Field(
        default_factory=list,
    )


class IntegrationIntegration(BaseIntegration):
    class AppConfigHandlerClass(APIPortAppConfig):
        CONFIG_CLASS = IntegrationAppConfig
