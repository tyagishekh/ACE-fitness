import pytest
from typing import cast

from app import GymService, create_app, recommend_calories, validate_member_payload


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_recommend_calories_for_known_goal():
    assert recommend_calories(70, "muscle-gain") == 2310


def test_validate_member_payload_rejects_invalid_goal():
    with pytest.raises(ValueError, match="Goal must be one of"):
        validate_member_payload(
            {
                "name": "Invalid Goal User",
                "age": 25,
                "weight_kg": 68,
                "goal": "cardio-only",
                "adherence_score": 75,
            }
        )


def test_service_add_member_updates_collection():
    service = GymService()
    created = cast(dict, service.add_member(
        {
            "name": "Priya Nair",
            "age": 26,
            "weight_kg": 59.5,
            "goal": "general-fitness",
            "adherence_score": 84,
        }
    ))

    # Access nested dict fields directly instead of attribute access
    assert created["program"]["name"] == "General Fitness Starter"
    assert service.get_dashboard_stats()["total_members"] == 3


def test_index_route_exposes_service_metadata(client):
    response = client.get("/")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["application"] == "ACEest Fitness & Gym API"
    assert "/members" in payload["available_endpoints"]


def test_get_members_returns_seed_data(client):
    response = client.get("/members")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["members"]) == 2
    assert payload["members"][0]["name"] == "Ananya Sharma"


def test_post_member_creates_new_member(client):
    response = client.post(
        "/members",
        json={
            "name": "Karan Patel",
            "age": 29,
            "weight_kg": 82,
            "goal": "muscle-gain",
            "adherence_score": 89,
            "membership_status": "active",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["id"] == 3
    assert payload["recommended_calories"] == 2706


def test_post_member_returns_400_for_bad_payload(client):
    response = client.post(
        "/members",
        json={
            "name": "",
            "age": 12,
            "weight_kg": 0,
            "goal": "fat-loss",
            "adherence_score": 120,
        },
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_get_unknown_member_returns_404(client):
    response = client.get("/members/99")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Member with id 99 was not found"


def test_stats_route_returns_summary(client):
    response = client.get("/stats")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_members"] == 2
    assert payload["active_members"] == 2
    assert payload["average_adherence"] == 89.5
