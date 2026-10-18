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
