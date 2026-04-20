from __future__ import annotations

import logging

from app.evaluators.base import EvaluatorBase
from app.evaluators.mfa_enforced import MfaEnforcedEvaluator
from app.evaluators.inactive_users import InactiveUsersEvaluator
from app.evaluators.branch_protection import BranchProtectionEvaluator
from app.evaluators.no_direct_push import NoDirectPushEvaluator
from app.evaluators.audit_logging import AuditLoggingEvaluator
from app.connectors.base import ConnectorBase, MockConnector
from app.config import settings

logger = logging.getLogger("panopticon.registry")

# Maps evaluator_type string -> evaluator class
EVALUATOR_REGISTRY: dict[str, type[EvaluatorBase]] = {
    "mfa_enforced": MfaEnforcedEvaluator,
    "no_inactive_users": InactiveUsersEvaluator,
    "branch_protection": BranchProtectionEvaluator,
    "no_direct_push": NoDirectPushEvaluator,
    "audit_logging": AuditLoggingEvaluator,
}


def get_evaluator(evaluator_type: str) -> EvaluatorBase:
    cls = EVALUATOR_REGISTRY.get(evaluator_type)
    if cls is None:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")
    return cls()


def get_connector(connector_type: str) -> ConnectorBase:
    """Return a real connector if credentials are configured, otherwise mock."""
    if connector_type == "okta" and settings.okta_domain and settings.okta_api_token:
        from app.connectors.okta import OktaConnector
        return OktaConnector()

    if connector_type == "github" and settings.github_token:
        from app.connectors.github import GitHubConnector
        return GitHubConnector()

    if connector_type == "aws" and settings.aws_access_key_id:
        from app.connectors.aws import AWSConnector
        return AWSConnector()

    logger.info(f"No credentials for {connector_type}, using mock connector")
    return MockConnector(_get_mock_data(connector_type))


def _get_mock_data(connector_type: str) -> dict:
    """Return realistic mock data for development."""
    if connector_type == "okta":
        return {
            "users": [
                {"id": "u1", "email": "alice@example.com", "status": "ACTIVE", "mfa_enrolled": True, "mfa_factors": ["okta_verify"], "last_login": "2026-04-18T10:00:00Z"},
                {"id": "u2", "email": "bob@example.com", "status": "ACTIVE", "mfa_enrolled": True, "mfa_factors": ["okta_verify", "sms"], "last_login": "2026-04-15T14:30:00Z"},
                {"id": "u3", "email": "charlie@example.com", "status": "ACTIVE", "mfa_enrolled": False, "mfa_factors": [], "last_login": "2026-03-01T09:00:00Z"},
                {"id": "u4", "email": "dana@example.com", "status": "ACTIVE", "mfa_enrolled": True, "mfa_factors": ["webauthn"], "last_login": "2026-04-19T16:00:00Z"},
                {"id": "u5", "email": "eve@example.com", "status": "DEPROVISIONED", "mfa_enrolled": False, "mfa_factors": [], "last_login": "2025-12-01T08:00:00Z"},
                {"id": "u6", "email": "frank@example.com", "status": "ACTIVE", "mfa_enrolled": False, "mfa_factors": [], "last_login": "2026-01-10T11:00:00Z"},
            ]
        }
    if connector_type == "github":
        return {
            "repos": [
                {"full_name": "org/api-service", "default_branch": "main", "branch_protection": {"enabled": True, "required_reviews": 1, "enforce_admins": True, "restrict_pushes": True, "dismiss_stale_reviews": True, "required_status_checks": True, "require_linear_history": False}},
                {"full_name": "org/web-app", "default_branch": "main", "branch_protection": {"enabled": True, "required_reviews": 2, "enforce_admins": False, "restrict_pushes": False, "dismiss_stale_reviews": False, "required_status_checks": True, "require_linear_history": False}},
                {"full_name": "org/infra-config", "default_branch": "main", "branch_protection": None},
            ]
        }
    if connector_type == "aws":
        return {
            "accounts": [
                {"account_id": "123456789012", "account_name": "prod-us", "cloudtrail_enabled": True, "is_logging": True, "trail_name": "org-trail"},
                {"account_id": "234567890123", "account_name": "prod-eu", "cloudtrail_enabled": True, "is_logging": True, "trail_name": "org-trail"},
            ]
        }
    return {}
