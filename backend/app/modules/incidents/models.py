from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.users.models import User
from app.shared.db.base import Base
from app.shared.db.constraints import enum_check


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        enum_check("category", IncidentCategory),
        enum_check("criticality", Criticality),
        enum_check("status", IncidentStatus),
        # Supports the operational queue: active incidents filtered by status and ordered by age.
        Index("ix_incidents_status_created_at", "status", "created_at"),
        UniqueConstraint("reporter_id", "idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[IncidentCategory] = mapped_column(Enum(IncidentCategory, native_enum=False, length=30))
    criticality: Mapped[Criticality] = mapped_column(Enum(Criticality, native_enum=False, length=10))
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus, native_enum=False, length=20), default=IncidentStatus.OPEN)
    location: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000))

    # No separate index: the unique (reporter_id, idempotency_key) constraint already serves lookups by reporter.
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)

    closed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closure_reason: Mapped[str | None] = mapped_column(String(500))

    # Sent by the client so a retried report does not create a second incident. Incidents created outside the API have none.
    idempotency_key: Mapped[UUID | None] = mapped_column(Uuid)

    version: Mapped[int] = mapped_column(default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    closed_by: Mapped[User | None] = relationship(foreign_keys=[closed_by_id])
