from itertools import product

import pytest

from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus

OPEN = IncidentStatus.OPEN
INVESTIGATING = IncidentStatus.INVESTIGATING
CLOSED = IncidentStatus.CLOSED
INCONCLUSIVE = IncidentStatus.INCONCLUSIVE

# Expected lifecycle, written independently from the implementation.
ALLOWED_TRANSITIONS = {
    (OPEN, INVESTIGATING),
    (INVESTIGATING, CLOSED),
    (INVESTIGATING, INCONCLUSIVE),
    (INVESTIGATING, OPEN),
}


def test_criticality_sorts_from_most_to_least_critical() -> None:
    shuffled = [Criticality.LOW, Criticality.HIGH, Criticality.MEDIUM]

    assert sorted(shuffled, key=lambda criticality: criticality.priority) == [
        Criticality.HIGH,
        Criticality.MEDIUM,
        Criticality.LOW,
    ]


@pytest.mark.parametrize("criticality", list(Criticality))
def test_every_criticality_has_a_priority(criticality: Criticality) -> None:
    assert isinstance(criticality.priority, int)


@pytest.mark.parametrize(
    ("status", "is_active"),
    [(OPEN, True), (INVESTIGATING, True), (CLOSED, False), (INCONCLUSIVE, False)],
)
def test_only_open_and_investigating_incidents_are_active(status: IncidentStatus, is_active: bool) -> None:
    assert status.is_active is is_active


@pytest.mark.parametrize(
    ("status", "is_final"),
    [(OPEN, False), (INVESTIGATING, False), (CLOSED, True), (INCONCLUSIVE, True)],
)
def test_only_closed_and_inconclusive_incidents_are_final(status: IncidentStatus, is_final: bool) -> None:
    assert status.is_final is is_final


@pytest.mark.parametrize(("current", "target"), list(product(IncidentStatus, repeat=2)))
def test_status_transitions_follow_the_incident_lifecycle(current: IncidentStatus, target: IncidentStatus) -> None:
    assert current.can_transition_to(target) is ((current, target) in ALLOWED_TRANSITIONS)


@pytest.mark.parametrize(
    ("enum", "expected_values"),
    [
        (
            IncidentCategory,
            {"VEHICLE_ACCIDENT", "ACCIDENT_WITH_VICTIMS", "ADVERSE_WEATHER", "MECHANICAL_PROBLEM", "ROAD_BLOCKAGE"},
        ),
        (Criticality, {"HIGH", "MEDIUM", "LOW"}),
        (IncidentStatus, {"OPEN", "INVESTIGATING", "CLOSED", "INCONCLUSIVE"}),
    ],
)
def test_enum_values_are_stable(enum: type[IncidentCategory | Criticality | IncidentStatus], expected_values: set[str]) -> None:
    # These values are part of the API contract and are stored in the database.
    assert {member.value for member in enum} == expected_values
