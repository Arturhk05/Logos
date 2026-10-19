from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus

# PostgreSQL text columns cannot store the NUL character; without this, such input fails with 500.
WITHOUT_NUL = r"^[^\x00]*$"


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class ReporterSummary(UserSummary):
    """The only place a phone is shown: the reporter of an incident's details (RN-13)."""

    phone: str


class IncidentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: IncidentCategory
    criticality: Criticality
    status: IncidentStatus
    location: str
    created_at: datetime
    assignee: UserSummary | None


class IncidentHistoryItem(IncidentSummary):
    closed_by: UserSummary | None
    closed_at: datetime | None


class IncidentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[IncidentHistoryItem]
    total: int
    page: int
    page_size: int


class IncidentQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[IncidentSummary]
    counts: dict[Criticality, int]


class IncidentEventResponse(BaseModel):
    """One entry of the incident's change log (RN-12). No previous status means the report."""

    model_config = ConfigDict(from_attributes=True)

    actor: UserSummary
    from_status: IncidentStatus | None
    to_status: IncidentStatus
    reason: str | None
    created_at: datetime


class IncidentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: IncidentCategory
    criticality: Criticality
    status: IncidentStatus
    location: str
    description: str
    reporter: ReporterSummary
    assignee: UserSummary | None
    closed_by: UserSummary | None
    closed_at: datetime | None
    closure_reason: str | None

    version: int
    created_at: datetime
    updated_at: datetime
    events: list[IncidentEventResponse]


class VersionedRequest(BaseModel):
    """Every change to an incident carries the version the user saw, so concurrent changes are detected (ADR-02)."""

    version: int


class StatusChangeRequest(VersionedRequest):
    status: IncidentStatus
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500, pattern=WITHOUT_NUL)] | None = None


class ReportIncidentRequest(BaseModel):
    category: IncidentCategory
    criticality: Criticality | None = None
    location: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200, pattern=WITHOUT_NUL)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000, pattern=WITHOUT_NUL)]


class IncidentConflict(BaseModel):
    detail: str
    current: IncidentDetail


class CategoryOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: IncidentCategory
    label: str
    suggested_criticality: Criticality
    criticality_locked: bool
