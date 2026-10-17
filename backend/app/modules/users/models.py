from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.users.enums import UserRole
from app.shared.db.base import Base
from app.shared.db.constraints import enum_check


class User(Base):
    __tablename__ = "users"
    __table_args__ = (enum_check("role", UserRole),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False, length=20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
