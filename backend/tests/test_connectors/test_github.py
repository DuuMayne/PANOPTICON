"""Mocked GitHub connector tests — verifies branch protection normalization."""
from unittest.mock import patch, MagicMock

from app.connectors.github import GitHubConnector


def _mock_repo_response():
    return {"default_branch": "main", "full_name": "org/api-service"}


def _mock_protection_response():
    return {
        "required_pull_request_reviews": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews": True,
        },
        "enforce_admins": {"enabled": True},
        "required_status_checks": {"strict": True, "contexts": []},
        "restrictions": {"users": [], "teams": []},
        "required_linear_history": {"enabled": False},
    }


@patch("app.connectors.github.httpx.get")
def test_fetch_protected_repo(mock_get):
    def side_effect(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "/protection" in url:
            resp.json.return_value = _mock_protection_response()
            resp.status_code = 200
        else:
            resp.json.return_value = _mock_repo_response()
        return resp

    mock_get.side_effect = side_effect

    connector = GitHubConnector()
    data = connector.fetch({"critical_repos": ["org/api-service"]})

    assert len(data["repos"]) == 1
    repo = data["repos"][0]
    assert repo["full_name"] == "org/api-service"
    assert repo["branch_protection"]["enabled"] is True
    assert repo["branch_protection"]["required_reviews"] == 2
    assert repo["branch_protection"]["restrict_pushes"] is True
    assert repo["branch_protection"]["enforce_admins"] is True


@patch("app.connectors.github.httpx.get")
def test_fetch_unprotected_repo(mock_get):
    import httpx

    def side_effect(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "/protection" in url:
            resp.status_code = 404
            return resp
        resp.json.return_value = _mock_repo_response()
        return resp

    mock_get.side_effect = side_effect

    connector = GitHubConnector()
    data = connector.fetch({"critical_repos": ["org/api-service"]})

    repo = data["repos"][0]
    assert repo["branch_protection"] is None


def test_fetch_no_repos_configured():
    connector = GitHubConnector()
    data = connector.fetch({"critical_repos": []})
    assert data["repos"] == []


def test_fetch_no_config():
    connector = GitHubConnector()
    data = connector.fetch({})
    assert data["repos"] == []


@patch("app.connectors.github.httpx.get")
def test_connection_test(mock_get):
    resp = MagicMock()
    resp.status_code = 200
    mock_get.return_value = resp

    connector = GitHubConnector()
    assert connector.test_connection() is True
