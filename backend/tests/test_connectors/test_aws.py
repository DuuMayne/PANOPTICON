"""Mocked AWS connector tests — verifies CloudTrail status checking."""
from unittest.mock import patch, MagicMock

from app.connectors.aws import AWSConnector


@patch("app.connectors.aws.boto3.Session")
def test_fetch_logging_enabled(mock_session_cls):
    ct_client = MagicMock()
    ct_client.describe_trails.return_value = {
        "trailList": [{"Name": "org-trail", "TrailARN": "arn:aws:cloudtrail:us-east-1:111:trail/org-trail"}]
    }
    ct_client.get_trail_status.return_value = {"IsLogging": True}

    session = MagicMock()
    session.client.return_value = ct_client
    mock_session_cls.return_value = session

    connector = AWSConnector()
    data = connector.fetch({"production_accounts": ["111111111111"]})

    assert len(data["accounts"]) == 1
    acct = data["accounts"][0]
    assert acct["account_id"] == "111111111111"
    assert acct["cloudtrail_enabled"] is True
    assert acct["is_logging"] is True


@patch("app.connectors.aws.boto3.Session")
def test_fetch_no_trails(mock_session_cls):
    ct_client = MagicMock()
    ct_client.describe_trails.return_value = {"trailList": []}

    session = MagicMock()
    session.client.return_value = ct_client
    mock_session_cls.return_value = session

    connector = AWSConnector()
    data = connector.fetch({"production_accounts": ["222222222222"]})

    acct = data["accounts"][0]
    assert acct["cloudtrail_enabled"] is False
    assert acct["is_logging"] is False


@patch("app.connectors.aws.boto3.Session")
def test_fetch_trail_not_logging(mock_session_cls):
    ct_client = MagicMock()
    ct_client.describe_trails.return_value = {
        "trailList": [{"Name": "stopped-trail", "TrailARN": "arn:aws:cloudtrail:us-east-1:333:trail/stopped"}]
    }
    ct_client.get_trail_status.return_value = {"IsLogging": False}

    session = MagicMock()
    session.client.return_value = ct_client
    mock_session_cls.return_value = session

    connector = AWSConnector()
    data = connector.fetch({"production_accounts": ["333333333333"]})

    acct = data["accounts"][0]
    assert acct["cloudtrail_enabled"] is True
    assert acct["is_logging"] is False


def test_fetch_no_accounts_configured():
    connector = AWSConnector()
    data = connector.fetch({"production_accounts": []})
    assert data["accounts"] == []


def test_fetch_empty_config():
    connector = AWSConnector()
    data = connector.fetch({})
    assert data["accounts"] == []


@patch("app.connectors.aws.boto3.client")
def test_connection_test(mock_client):
    sts = MagicMock()
    sts.get_caller_identity.return_value = {"Account": "111"}
    mock_client.return_value = sts

    connector = AWSConnector()
    assert connector.test_connection() is True


@patch("app.connectors.aws.boto3.client")
def test_connection_test_failure(mock_client):
    mock_client.side_effect = Exception("No credentials")
    connector = AWSConnector()
    assert connector.test_connection() is False
