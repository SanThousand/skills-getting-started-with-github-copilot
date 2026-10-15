from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    """Give each test an isolated copy of the in-memory activity data."""
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_includes_the_sample_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert "Basketball Team" in activities
    assert "Science Club" in activities


def test_signup_rejects_a_duplicate_registration(client):
    signup_url = "/activities/Art%20Studio/signup"
    params = {"email": "new-student@mergington.edu"}

    first_response = client.post(signup_url, params=params)
    duplicate_response = client.post(signup_url, params=params)

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student is already signed up"
    assert client.get("/activities").json()["Art Studio"]["participants"].count(
        "new-student@mergington.edu"
    ) == 1


def test_signup_rejects_unknown_activities(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_a_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Unregistered michael@mergington.edu from Chess Club"
    )
    assert "michael@mergington.edu" not in client.get("/activities").json()["Chess Club"][
        "participants"
    ]


def test_unregister_returns_not_found_for_an_unregistered_student(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"
