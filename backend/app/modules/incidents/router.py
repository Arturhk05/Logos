from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import JSONResponse

from app.modules.auth.dependencies import CurrentUser, require_role
from app.modules.incidents.dependencies import get_incident_service
from app.modules.incidents.enums import Criticality, IncidentCategory
from app.modules.incidents.schemas import (
    IncidentConflict,
    IncidentDetail,
    IncidentQueueResponse,
    ReportIncidentRequest,
    StatusChangeRequest,
    VersionedRequest,
)
from app.modules.incidents.service import IncidentReport, IncidentService
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import ConflictError

router = APIRouter(prefix="/incidents", tags=["incidents"])

CentralUser = Annotated[User, Depends(require_role(UserRole.ANALYST, UserRole.SUPERVISOR))]
DriverUser = Annotated[User, Depends(require_role(UserRole.DRIVER))]
Service = Annotated[IncidentService, Depends(get_incident_service)]

CONFLICT_RESPONSES: dict[int | str, dict[str, Any]] = {status.HTTP_409_CONFLICT: {"model": IncidentConflict}}


def _conflict_response(error: ConflictError) -> JSONResponse:
    # Built here rather than in the global handler: `shared` cannot import this module's schemas,
    # and serializing the ORM object directly would leak fields such as password_hash.
    body = IncidentConflict(detail=error.message, current=IncidentDetail.model_validate(error.current))
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump(mode="json"))


@router.get("", response_model=IncidentQueueResponse)
def list_active_incidents(
    _: CentralUser,
    service: Service,
    criticality: Annotated[list[Criticality] | None, Query()] = None,
    category: Annotated[list[IncidentCategory] | None, Query()] = None,
) -> IncidentQueueResponse:
    queue = service.list_active(criticality or (), category or ())
    return IncidentQueueResponse.model_validate(queue)


@router.post("", response_model=IncidentDetail, status_code=status.HTTP_201_CREATED)
def report_incident(
    request: ReportIncidentRequest, idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")], user: DriverUser, service: Service
) -> IncidentDetail:
    report = IncidentReport(
        category=request.category,
        location=request.location,
        description=request.description,
        idempotency_key=idempotency_key,
        criticality=request.criticality,
    )
    return IncidentDetail.model_validate(service.report(user, report))


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, user: CurrentUser, service: Service) -> IncidentDetail:
    return IncidentDetail.model_validate(service.get_visible_to(incident_id, user))


@router.post("/{incident_id}/assume", response_model=IncidentDetail, responses=CONFLICT_RESPONSES)
def assume_incident(incident_id: int, request: VersionedRequest, user: CentralUser, service: Service) -> IncidentDetail | JSONResponse:
    try:
        incident = service.assume(incident_id, user, request.version)
    except ConflictError as error:
        return _conflict_response(error)
    return IncidentDetail.model_validate(incident)


@router.patch("/{incident_id}/status", response_model=IncidentDetail, responses=CONFLICT_RESPONSES)
def change_incident_status(
    incident_id: int, request: StatusChangeRequest, user: CentralUser, service: Service
) -> IncidentDetail | JSONResponse:
    try:
        incident = service.change_status(incident_id, user, request.version, request.status, request.reason)
    except ConflictError as error:
        return _conflict_response(error)
    return IncidentDetail.model_validate(incident)
