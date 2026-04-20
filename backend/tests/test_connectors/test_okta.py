"""Mocked Okta connector tests — verifies data normalization without real API calls."""
from unittest.mock import patch, MagicMock

from app.connectors.okta import OktaConnector


def _mock_users_response():
    return [
        {
            "id": "00u1",
            "profile": {"email": "alice@example.com", "login": "alice@example.com"},
            "status": "ACTIVE",
            "lastLogin": "2026-04-18T10:00:00.000Z",
            "created": "2025-01-01T00:00:00.000Z",
        },
        {
            "id": "00u2",
            "profile": {"email": "bob@example.com", "login": "bob@example.com"},
            "status": "ACTIVE",
            "lastLogin": None,
            "created": "2025-06-01T00:00:00.000Z",
        },
    ]


def _mock_factors_response(user_id):
    if user_id == "00u1":
        return [{"factorType": "push", "status": "ACTIVE", "provider": "OKTA"}]
    return []


@patch("app.connectors.okta.httpx.get")
def test_fetch_normalizes_users(mock_get):
    # Set up mock responses
    users_resp = MagicMock()
    users_resp.json.return_value = _mock_users_response()
    users_resp.raise_for_status = MagicMock()
    users_resp.headers = {}  # No pagination

    def side_effect(url, **kwargs):
        if "/factors" in url:
            resp = MagicMock()
            user_id = url.split("/users/")[1].split("/factors")[0]
            resp.json.return_value = _mock_factors_response(user_id)
            resp.raise_for_status = MagicMock()
            return resp
        return users_resp

    mock_get.side_effect = side_effect

    connector = OktaConnector()
    data = connector.fetch({})

    assert "users" in data
    assert len(data["users"]) == 2

    alice = data["users"][0]
    assert alice["email"] == "alice@example.com"
    assert alice["status"] == "ACTIVE"
    assert alice["mfa_enrolled"] is True
    assert "push" in alice["mfa_factors"]

    bob = data["users"][1]
    assert bob["mfa_enrolled"] is False
    assert bob["mfa_factors"] == []


@patch("app.connectors.okta.httpx.get")
def test_pagination_follows_link_header(mock_get):
    page1_resp = MagicMock()
    page1_resp.json.return_value = [_mock_users_response()[0]]
    page1_resp.raise_for_status = MagicMock()
    page1_resp.headers = {"link": '<https://test.okta.com/api/v1/users?after=abc>; rel="next"'}

    page2_resp = MagicMock()
    page2_resp.json.return_value = [_mock_users_response()[1]]
    page2_resp.raise_for_status = MagicMock()
    page2_resp.headers = {}

    call_count = {"n": 0}

    def side_effect(url, **kwargs):
        if "/factors" in url:
            resp = MagicMock()
            user_id = url.split("/users/")[1].split("/factors")[0]
            resp.json.return_value = _mock_factors_response(user_id)
            resp.raise_for_status = MagicMock()
            return resp
        call_count["n"] += 1
        return page1_resp if call_count["n"] == 1 else page2_resp

    mock_get.side_effect = side_effect

    connector = OktaConnector()
    data = connector.fetch({})
    assert len(data["users"]) == 2


@patch("app.connectors.okta.httpx.get")
def test_connection_test(mock_get):
    resp = MagicMock()
    resp.status_code = 200
    mock_get.return_value = resp

    connector = OktaConnector()
    assert connector.test_connection() is True


@patch("app.connectors.okta.httpx.get")
def test_connection_test_failure(mock_get):
    mock_get.side_effect = Exception("Connection refused")
    connector = OktaConnector()
    assert connector.test_connection() is False
