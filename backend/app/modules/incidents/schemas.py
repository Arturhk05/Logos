from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class IncidentQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: IncidentCategory
    criticality: Criticality
    status: IncidentStatus
    location: str
    created_at: datetime
    assignee: UserSummary | None


class IncidentQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[IncidentQueueItem]
    counts: dict[Criticality, int]
