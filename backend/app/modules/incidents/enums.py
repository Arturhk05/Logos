from enum import StrEnum


class IncidentCategory(StrEnum):
    VEHICLE_ACCIDENT = "VEHICLE_ACCIDENT"
    ACCIDENT_WITH_VICTIMS = "ACCIDENT_WITH_VICTIMS"
    ADVERSE_WEATHER = "ADVERSE_WEATHER"
    MECHANICAL_PROBLEM = "MECHANICAL_PROBLEM"
    ROAD_BLOCKAGE = "ROAD_BLOCKAGE"


class Criticality(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def priority(self) -> int:
        """Lower value means more urgent, so incidents can be sorted from most to least critical."""
        return _CRITICALITY_PRIORITY[self]


_CRITICALITY_PRIORITY = {
    Criticality.HIGH: 0,
    Criticality.MEDIUM: 1,
    Criticality.LOW: 2,
}


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"
    INCONCLUSIVE = "INCONCLUSIVE"

    @property
    def is_active(self) -> bool:
        """Active incidents are the ones shown in the operational queue."""
        return self in {IncidentStatus.OPEN, IncidentStatus.INVESTIGATING}

    @property
    def is_final(self) -> bool:
        """Final incidents have no outgoing transitions, so they can no longer change status."""
        return not _ALLOWED_TRANSITIONS[self]

    def can_transition_to(self, target: IncidentStatus) -> bool:
        """Whether moving from this status to `target` is allowed by the incident lifecycle."""
        return target in _ALLOWED_TRANSITIONS[self]


_ALLOWED_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.INVESTIGATING}),
    IncidentStatus.INVESTIGATING: frozenset({IncidentStatus.CLOSED, IncidentStatus.INCONCLUSIVE, IncidentStatus.OPEN}),
    IncidentStatus.CLOSED: frozenset(),
    IncidentStatus.INCONCLUSIVE: frozenset(),
}
