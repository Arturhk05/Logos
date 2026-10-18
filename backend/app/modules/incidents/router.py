from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.auth.dependencies import CurrentUser, require_role
from app.modules.incidents.dependencies import get_incident_service
from app.modules.incidents.enums import Criticality, IncidentCategory
from app.modules.incidents.schemas import IncidentDetail, IncidentQueueResponse
from app.modules.incidents.service import IncidentService
from app.modules.users.enums import UserRole
from app.modules.users.models import User

router = APIRouter(prefix="/incidents", tags=["incidents"])

CentralUser = Annotated[User, Depends(require_role(UserRole.ANALYST, UserRole.SUPERVISOR))]
Service = Annotated[IncidentService, Depends(get_incident_service)]


@router.get("", response_model=IncidentQueueResponse)
def list_active_incidents(
    _: CentralUser,
    service: Service,
    criticality: Annotated[list[Criticality] | None, Query()] = None,
    category: Annotated[list[IncidentCategory] | None, Query()] = None,
) -> IncidentQueueResponse:
    queue = service.list_active(criticality or (), category or ())
    return IncidentQueueResponse.model_validate(queue)


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: int, user: CurrentUser, service: Service) -> IncidentDetail:
    return IncidentDetail.model_validate(service.get_visible_to(incident_id, user))
