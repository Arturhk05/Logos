"""Create the demo users and sample incidents. Safe to run on every deploy: existing data is kept."""

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.security import hash_password
from app.modules.incidents.enums import Criticality, IncidentCategory, IncidentStatus
from app.modules.incidents.models import Incident
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import SqlAlchemyUserRepository
from app.shared.db.session import get_session_factory

DEMO_PASSWORD = "logos123"  # noqa: S105 (public demo credential, shown on the login screen)

DEMO_USERS: tuple[tuple[str, UserRole], ...] = (
    ("camila", UserRole.ANALYST),
    ("lucas", UserRole.ANALYST),
    ("roberto", UserRole.SUPERVISOR),
    ("jose", UserRole.DRIVER),
    # Extra drivers spread the sample incidents, so jose's "my reports" shows only his own.
    ("maria", UserRole.DRIVER),
    ("antonio", UserRole.DRIVER),
    ("paulo", UserRole.DRIVER),
)

# The brief asks how the central handles 100 simultaneous incidents; the closed ones fill a few history pages.
INCIDENTS_PER_STATUS: dict[IncidentStatus, int] = {
    IncidentStatus.OPEN: 65,
    IncidentStatus.INVESTIGATING: 35,
    IncidentStatus.CLOSED: 28,
    IncidentStatus.INCONCLUSIVE: 12,
}

# Fixed so every environment shows the same demo data.
RANDOM_SEED = 2026

CATEGORY_WEIGHTS: dict[IncidentCategory, int] = {
    IncidentCategory.MECHANICAL_PROBLEM: 30,
    IncidentCategory.ROAD_BLOCKAGE: 22,
    IncidentCategory.ADVERSE_WEATHER: 20,
    IncidentCategory.VEHICLE_ACCIDENT: 20,
    IncidentCategory.ACCIDENT_WITH_VICTIMS: 8,
}

# Drivers usually keep the suggested criticality, but sometimes change it (RN-10), except for victims.
CRITICALITY_WEIGHTS: dict[IncidentCategory, dict[Criticality, int]] = {
    IncidentCategory.ACCIDENT_WITH_VICTIMS: {Criticality.HIGH: 1},
    IncidentCategory.VEHICLE_ACCIDENT: {Criticality.HIGH: 7, Criticality.MEDIUM: 3},
    IncidentCategory.ROAD_BLOCKAGE: {Criticality.HIGH: 2, Criticality.MEDIUM: 3, Criticality.LOW: 5},
    IncidentCategory.ADVERSE_WEATHER: {Criticality.HIGH: 1, Criticality.MEDIUM: 5, Criticality.LOW: 4},
    IncidentCategory.MECHANICAL_PROBLEM: {Criticality.HIGH: 1, Criticality.MEDIUM: 5, Criticality.LOW: 4},
}

ROADS: tuple[tuple[str, str], ...] = (
    ("BR-116", "Curitiba/PR"),
    ("BR-116", "Registro/SP"),
    ("BR-101", "Joinville/SC"),
    ("BR-101", "Palhoça/SC"),
    ("BR-277", "São José dos Pinhais/PR"),
    ("BR-376", "Ponta Grossa/PR"),
    ("BR-381", "Betim/MG"),
    ("BR-040", "Juiz de Fora/MG"),
    ("BR-153", "Goiânia/GO"),
    ("BR-163", "Sorriso/MT"),
    ("BR-364", "Cuiabá/MT"),
    ("BR-050", "Uberlândia/MG"),
    ("SP-330", "Campinas/SP"),
    ("SP-348", "Jundiaí/SP"),
    ("BR-290", "Porto Alegre/RS"),
)

DESCRIPTIONS: dict[IncidentCategory, tuple[str, ...]] = {
    IncidentCategory.VEHICLE_ACCIDENT: (
        "Colisão traseira entre o caminhão e um carro de passeio. Sem feridos, veículos no acostamento.",
        "Caminhão tombou na curva e a carga ficou espalhada pela faixa da direita.",
        "Batida lateral ao mudar de faixa. Retrovisor e para-choque danificados.",
        "Engavetamento com três veículos. Trânsito parado nos dois sentidos.",
    ),
    IncidentCategory.ACCIDENT_WITH_VICTIMS: (
        "Colisão frontal com um carro de passeio. Dois feridos, SAMU já acionado.",
        "Motociclista atingido na lateral do caminhão. Vítima consciente, aguardando socorro.",
        "Capotamento na pista contrária com vítima presa às ferragens. Bombeiros a caminho.",
    ),
    IncidentCategory.ADVERSE_WEATHER: (
        "Neblina densa, visibilidade abaixo de 50 metros. Seguindo em velocidade reduzida.",
        "Chuva forte com acúmulo de água na pista. Risco de aquaplanagem.",
        "Granizo forte no trecho. Parei no posto até a chuva diminuir.",
        "Ventos fortes empurrando a carreta para o acostamento.",
    ),
    IncidentCategory.MECHANICAL_PROBLEM: (
        "Pneu estourado no eixo traseiro. Parado no acostamento aguardando borracharia.",
        "Superaquecimento do motor, luz de alerta acesa. Parei para esfriar.",
        "Falha no sistema de freios a ar. Veículo parado em local seguro.",
        "Bateria descarregada, o caminhão não dá partida.",
        "Vazamento de óleo embaixo da cabine. Preciso de guincho.",
    ),
    IncidentCategory.ROAD_BLOCKAGE: (
        "Pista interditada pela polícia rodoviária por causa de um acidente à frente.",
        "Manifestação bloqueando os dois sentidos da rodovia.",
        "Queda de barreira cobrindo metade da pista. Passagem em sistema pare e siga.",
        "Árvore caída atravessada na pista após o temporal.",
        "Obra na pista com fila de mais de 5 km.",
    ),
}

CLOSURE_REASONS: dict[IncidentStatus, tuple[str, ...]] = {
    IncidentStatus.CLOSED: (
        "Guincho chegou e o veículo foi levado à oficina. Motorista seguiu viagem em veículo reserva.",
        "Pista liberada pela polícia rodoviária. Viagem retomada.",
        "Socorro prestado e cliente avisado sobre o atraso na entrega.",
        "Problema resolvido no local pela equipe de manutenção.",
        "Condições da pista normalizadas. Motorista confirmou a retomada.",
    ),
    IncidentStatus.INCONCLUSIVE: (
        "Não foi possível contato com o motorista após várias tentativas.",
        "Ocorrência não confirmada no local pela equipe enviada.",
        "Reporte duplicado de outro incidente já em tratamento.",
    ),
}


def seed_users(session: Session) -> int:
    """Create the demo users that do not exist yet and return how many were created."""
    users = SqlAlchemyUserRepository(session)
    missing = [(username, role) for username, role in DEMO_USERS if users.get_by_username(username) is None]
    for username, role in missing:
        session.add(User(username=username, password_hash=hash_password(DEMO_PASSWORD), role=role))
    session.flush()
    return len(missing)


def seed_incidents(session: Session) -> int:
    """Create the sample incidents when there are none yet and return how many were created.

    Any existing incident means the environment is already in use, so nothing is added or changed.
    Requires the demo users, so it runs after `seed_users`.
    """
    if session.scalar(select(Incident.id).limit(1)) is not None:
        return 0

    users = list(session.scalars(select(User).where(User.username.in_(username for username, _ in DEMO_USERS))))
    drivers = [user for user in users if user.role is UserRole.DRIVER]
    central = [user for user in users if user.role is not UserRole.DRIVER]
    supervisors = [user for user in central if user.role is UserRole.SUPERVISOR]

    rng = random.Random(RANDOM_SEED)  # noqa: S311 (sample data, not security)
    now = datetime.now(UTC)
    incidents = [
        _build_incident(rng, now, status, drivers, central, supervisors)
        for status, amount in INCIDENTS_PER_STATUS.items()
        for _ in range(amount)
    ]
    session.add_all(incidents)
    session.flush()
    return len(incidents)


def _build_incident(
    rng: random.Random,
    now: datetime,
    status: IncidentStatus,
    drivers: list[User],
    central: list[User],
    supervisors: list[User],
) -> Incident:
    category = rng.choices(list(CATEGORY_WEIGHTS), weights=list(CATEGORY_WEIGHTS.values()))[0]
    criticality_weights = CRITICALITY_WEIGHTS[category]
    criticality = rng.choices(list(criticality_weights), weights=list(criticality_weights.values()))[0]
    road, city = rng.choice(ROADS)

    incident = Incident(
        category=category,
        criticality=criticality,
        status=status,
        location=f"{road}, km {rng.randint(1, 600)} - {city}",
        description=rng.choice(DESCRIPTIONS[category]),
        reporter_id=rng.choice(drivers).id,
        version=1,
    )

    if status.is_active:
        # Active incidents are recent, as in a live queue; closed ones go back a few days.
        incident.created_at = now - timedelta(minutes=rng.uniform(2, 8 * 60))
    else:
        incident.created_at = now - timedelta(hours=rng.uniform(12, 7 * 24))
    incident.updated_at = incident.created_at

    if status is IncidentStatus.OPEN:
        return incident

    assignee = rng.choice(central)
    incident.assignee_id = assignee.id
    incident.version = 2
    if status is IncidentStatus.INVESTIGATING:
        age = now - incident.created_at
        incident.updated_at = incident.created_at + age * rng.uniform(0.1, 0.9)
        return incident

    # Supervisors sometimes close incidents assigned to analysts (RN-03).
    closer = rng.choice(supervisors) if rng.random() < 0.2 else assignee
    incident.closed_by_id = closer.id
    incident.closed_at = incident.created_at + timedelta(minutes=rng.uniform(20, 10 * 60))
    incident.closure_reason = rng.choice(CLOSURE_REASONS[status])
    incident.updated_at = incident.closed_at
    incident.version = 3
    return incident


def main() -> None:
    with get_session_factory().begin() as session:
        users_created = seed_users(session)
        incidents_created = seed_incidents(session)
    print(f"Demo users created: {users_created}")
    print(f"Sample incidents created: {incidents_created}")


if __name__ == "__main__":
    main()
