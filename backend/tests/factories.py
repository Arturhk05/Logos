"""Helpers to create test data with sensible defaults.

`build_*` functions create objects in memory only, for unit tests.
`create_*` functions also save them to the database, for integration tests, letting the
database generate the ids.
"""

from itertools import count
from typing import Any

from sqlalchemy.orm import Session

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.users.enums import UserRole
from app.modules.users.models import User

_sequence = count(1)


def build_user(role: UserRole = UserRole.ANALYST, **overrides: Any) -> User:
    number = next(_sequence)
    fields: dict[str, Any] = {
        "id": number,
        "username": f"user{number}",
        "password_hash": "not-a-real-hash",
        "role": role,
        # Every driver has a phone (RN-13); area code 00 so it can never be a real number.
        "phone": f"55009{number:08d}" if role is UserRole.DRIVER else None,
    }
    return User(**(fields | overrides))


def build_incident(reporter: User, **overrides: Any) -> Incident:
    fields: dict[str, Any] = {
        "id": next(_sequence),
        "category": IncidentCategory.MECHANICAL_PROBLEM,
        "criticality": Criticality.MEDIUM,
        "status": IncidentStatus.OPEN,
        "location": "BR-116, km 230",
        "description": "Pneu furado no acostamento",
        "reporter_id": reporter.id,
        "version": 1,
    }
    return Incident(**(fields | overrides))


def create_user(session: Session, role: UserRole = UserRole.ANALYST, **overrides: Any) -> User:
    user = build_user(role, **({"id": None} | overrides))
    session.add(user)
    session.flush()
    return user


def create_incident(session: Session, reporter: User, **overrides: Any) -> Incident:
    incident = build_incident(reporter, **({"id": None} | overrides))
    session.add(incident)
    session.flush()
    session.refresh(incident)
    return incident
