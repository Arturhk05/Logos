from app.modules.incidents.repository import SqlAlchemyIncidentRepository
from app.modules.incidents.service import IncidentService
from app.shared.db.session import SessionDep


def get_incident_service(session: SessionDep) -> IncidentService:
    return IncidentService(SqlAlchemyIncidentRepository(session))
