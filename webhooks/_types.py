from pydantic import BaseModel


class PortContext(BaseModel):
    run_id: str
    blueprint: str