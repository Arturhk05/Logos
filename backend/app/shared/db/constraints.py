from enum import StrEnum

from sqlalchemy import CheckConstraint


def enum_check(column: str, enum: type[StrEnum]) -> CheckConstraint:
    """Restrict a string column to the values of `enum` at the database level.

    Used instead of `Enum(create_constraint=True)`, which Alembic autogenerate renders
    as duplicated constraints.
    """
    allowed_values = ", ".join(f"'{member.value}'" for member in enum)
    return CheckConstraint(f"{column} IN ({allowed_values})", name=f"{column}_valid")
