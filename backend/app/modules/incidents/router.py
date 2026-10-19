from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, status
from fastapi.responses import JSONResponse

from app.modules.auth.dependencies import CurrentUser, require_role
from app.modules.incidents.dependencies import get_incident_service
from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.schemas import (
    CategoryOptionResponse,
    IncidentConflict,
    IncidentDetail,
    IncidentHistoryResponse,
    IncidentQueueResponse,
    IncidentSummary,
    ReportIncidentRequest,
    StatusChangeRequest,
    VersionedRequest,
)
from app.modules.incidents.service import IncidentReport, IncidentService, category_options
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.shared.errors import ConflictError

router = APIRouter(prefix="/incidents", tags=["incidents"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])

CentralUser = Annotated[User, Depends(require_role(UserRole.ANALYST, UserRole.SUPERVISOR))]
DriverUser = Annotated[User, Depends(require_role(UserRole.DRIVER))]
Service = Annotated[IncidentService, Depends(get_incident_service)]
# Bounded by the id column (PostgreSQL INTEGER): a larger value would fail in the database with 500.
IncidentId = Annotated[int, Path(ge=1, le=2_147_483_647)]

MAX_HISTORY_PAGE = 100_000

CONFLICT_RESPONSES: dict[int | str, dict[str, Any]] = {status.HTTP_409_CONFLICT: {"model": IncidentConflict}}


def _conflict_response(error: ConflictError) -> JSONResponse:
    # Built here rather than in the global handler: `shared` cannot import this module's schemas,
    # and serializing the ORM object directly would leak fields such as password_hash.
    body = IncidentConflict(detail=error.message, current=IncidentDetail.model_validate(error.current))
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump(mode="json"))


@router.get("", response_model=IncidentQueueResponse)
def list_active_incidents(
    user: CentralUser,
    service: Service,
    criticality: Annotated[list[Criticality] | None, Query()] = None,
    category: Annotated[list[IncidentCategory] | None, Query()] = None,
    assigned_to_me: bool = False,
) -> IncidentQueueResponse:
    queue = service.list_active(criticality or (), category or (), assignee_id=user.id if assigned_to_me else None)
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


@router.get("/{incident_id:int}", response_model=IncidentDetail)
def get_incident(incident_id: IncidentId, user: CurrentUser, service: Service) -> IncidentDetail:
    return IncidentDetail.model_validate(service.get_visible_to(incident_id, user))


@router.post("/{incident_id:int}/assume", response_model=IncidentDetail, responses=CONFLICT_RESPONSES)
def assume_incident(
    incident_id: IncidentId, request: VersionedRequest, user: CentralUser, service: Service
) -> IncidentDetail | JSONResponse:
    try:
        incident = service.assume(incident_id, user, request.version)
    except ConflictError as error:
        return _conflict_response(error)
    return IncidentDetail.model_validate(incident)


@router.patch("/{incident_id:int}/status", response_model=IncidentDetail, responses=CONFLICT_RESPONSES)
def change_incident_status(
    incident_id: IncidentId, request: StatusChangeRequest, user: CentralUser, service: Service
) -> IncidentDetail | JSONResponse:
    try:
        incident = service.change_status(incident_id, user, request.version, request.status, request.reason)
    except ConflictError as error:
        return _conflict_response(error)
    return IncidentDetail.model_validate(incident)


@router.get("/mine", response_model=list[IncidentSummary])
def list_my_incidents(user: DriverUser, service: Service) -> list[IncidentSummary]:
    return [IncidentSummary.model_validate(incident) for incident in service.list_reported_by(user)]


@router.get("/history", response_model=IncidentHistoryResponse)
def list_incident_history(
    _: CentralUser,
    service: Service,
    statuses: Annotated[list[IncidentStatus] | None, Query(alias="status")] = None,
    criticality: Annotated[list[Criticality] | None, Query()] = None,
    category: Annotated[list[IncidentCategory] | None, Query()] = None,
    page: Annotated[int, Query(ge=1, le=MAX_HISTORY_PAGE)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> IncidentHistoryResponse:
    history = service.list_closed(page, page_size, statuses or (), criticality or (), category or ())
    return IncidentHistoryResponse.model_validate(history)


@categories_router.get("", response_model=list[CategoryOptionResponse])
def list_categories(_: CurrentUser) -> list[CategoryOptionResponse]:
    return [CategoryOptionResponse.model_validate(option) for option in category_options()]
