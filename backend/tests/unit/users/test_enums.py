from app.modules.users.enums import UserRole


def test_user_role_values_are_stable() -> None:
    assert {role.value for role in UserRole} == {"ANALYST", "SUPERVISOR", "DRIVER"}
