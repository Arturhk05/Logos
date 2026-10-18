from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.incidents.repository import SqlAlchemyIncidentRepository
from app.modules.incidents.service import IncidentService
from app.shared.db.session import get_session


def get_incident_service(session: Annotated[Session, Depends(get_session)]) -> IncidentService:
    return IncidentService(SqlAlchemyIncidentRepository(session))
