import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.role import Role
from app.models.user import User
from app.services.bootstrap import seed_roles
from main import app


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_roles(db)


def register(
    client: TestClient,
    email: str,
    password: str = "strongpass123",
    role_name: str | None = None,
) -> dict:
    payload = {"email": email, "full_name": "Test User", "password": password}
    if role_name is not None:
        payload["role_name"] = role_name
    response = client.post(
        "/auth/register",
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = "strongpass123") -> str:
    response = client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def assign_role(email: str, role_name: str) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        role = db.scalar(select(Role).where(Role.name == role_name))
        assert user is not None
        assert role is not None
        user.roles.append(role)
        db.commit()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_register_login_and_profile():
    reset_database()
    with TestClient(app) as client:
        user = register(client, "person@example.com")
        token = login(client, "person@example.com")
        response = client.get("/auth/me", headers=auth_header(token))

    assert user["roles"][0]["name"] == "Participant"
    assert response.status_code == 200
    assert response.json()["email"] == "person@example.com"


def test_register_can_select_non_admin_role():
    reset_database()
    with TestClient(app) as client:
        user = register(client, "organizer-role@example.com", role_name="Organizer")

    assert [role["name"] for role in user["roles"]] == ["Organizer"]


def test_register_cannot_select_admin_role():
    reset_database()
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={
                "email": "admin-role@example.com",
                "full_name": "Test User",
                "password": "strongpass123",
                "role_name": "Admin",
            },
        )

    assert response.status_code == 403


def test_admin_can_assign_role_case_insensitively():
    reset_database()
    with TestClient(app) as client:
        admin = register(client, "case-admin@example.com")
        user = register(client, "case-user@example.com")
        assign_role("case-admin@example.com", "Admin")
        admin_token = login(client, "case-admin@example.com")

        response = client.post(
            "/roles/assign",
            json={"user_id": user["id"], "role_name": "admin"},
            headers=auth_header(admin_token),
        )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Admin role assigned to case-user@example.com"


def test_event_registration_ticket_and_attendance_flow():
    reset_database()
    with TestClient(app) as client:
        register(client, "organizer@example.com")
        register(client, "participant@example.com")
        assign_role("organizer@example.com", "Organizer")

        organizer_token = login(client, "organizer@example.com")
        participant_token = login(client, "participant@example.com")

        category_response = client.post(
            "/categories",
            json={"name": "Technology", "description": "Tech events"},
            headers=auth_header(organizer_token),
        )
        assert category_response.status_code == 201, category_response.text

        event_response = client.post(
            "/events",
            json={
                "name": "FastAPI Workshop",
                "description": "Hands-on API session",
                "start_date": "2030-01-10T09:00:00Z",
                "end_date": "2030-01-10T17:00:00Z",
                "venue": "Main Hall",
                "capacity": 1,
                "category_id": category_response.json()["id"],
            },
            headers=auth_header(organizer_token),
        )
        assert event_response.status_code == 201, event_response.text
        event_id = event_response.json()["id"]

        registration_response = client.post(
            "/registrations",
            json={"event_id": event_id},
            headers=auth_header(participant_token),
        )
        assert registration_response.status_code == 201, registration_response.text
        registration_id = registration_response.json()["id"]

        duplicate_response = client.post(
            "/registrations",
            json={"event_id": event_id},
            headers=auth_header(participant_token),
        )
        assert duplicate_response.status_code == 409

        ticket_response = client.post(
            "/tickets",
            json={"registration_id": registration_id},
            headers=auth_header(participant_token),
        )
        assert ticket_response.status_code == 201, ticket_response.text
        ticket_number = ticket_response.json()["ticket_number"]
        assert ticket_response.json()["qr_code"]

        validation_response = client.post(
            f"/tickets/{ticket_number}/validate",
            headers=auth_header(organizer_token),
        )
        assert validation_response.status_code == 200
        assert validation_response.json()["is_valid"] is True

        attendance_response = client.post(
            "/attendance",
            json={"ticket_number": ticket_number},
            headers=auth_header(organizer_token),
        )
        assert attendance_response.status_code == 201, attendance_response.text

        summary_response = client.get(
            f"/attendance/{event_id}/summary",
            headers=auth_header(organizer_token),
        )
        assert summary_response.status_code == 200
        assert summary_response.json()["attended_count"] == 1


def test_dashboard_stats_for_organizer():
    reset_database()
    with TestClient(app) as client:
        register(client, "organizer2@example.com")
        assign_role("organizer2@example.com", "Organizer")
        token = login(client, "organizer2@example.com")

        response = client.get("/dashboard/stats", headers=auth_header(token))

    assert response.status_code == 200
    assert set(response.json()) == {
        "total_events",
        "total_participants",
        "upcoming_events",
        "completed_events",
    }


def test_create_event_validation_error_is_json_response():
    reset_database()
    with TestClient(app) as client:
        register(client, "event-admin@example.com")
        assign_role("event-admin@example.com", "Admin")
        token = login(client, "event-admin@example.com")

        response = client.post(
            "/events",
            json={
                "name": "music",
                "description": "concert",
                "start_date": "2026-06-16",
                "end_date": "2026-06-16",
                "venue": "chennai",
                "capacity": 50000,
                "category_id": 1,
                "organizer_id": 2,
            },
            headers=auth_header(token),
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "Validation failed"
