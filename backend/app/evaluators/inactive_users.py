from __future__ import annotations

from datetime import datetime, timezone, timedelta

from app.evaluators.base import EvaluatorBase, EvaluationResult, FailingResource


class InactiveUsersEvaluator(EvaluatorBase):
    """Check that no active users have been inactive beyond the threshold.

    Expected data from connector (same as mfa_enforced — shared Okta connector):
    {
        "users": [
            {
                "id": "okta-user-id",
                "email": "user@example.com",
                "status": "ACTIVE",
                "last_login": "2026-01-10T11:00:00Z"
            }
        ]
    }

    Config:
    {
        "inactivity_threshold_days": 90
    }
    """

    def evaluate(self, data: dict, config: dict) -> EvaluationResult:
        users = data.get("users", [])
        if not users:
            return EvaluationResult(
                status="error",
                summary="No user data returned from connector",
                metadata={"user_count": 0},
            )

        threshold_days = config.get("inactivity_threshold_days", 90)
        cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)
        active_users = [u for u in users if u.get("status") == "ACTIVE"]

        stale = []
        for u in active_users:
            last_login = u.get("last_login")
            if not last_login:
                stale.append(u)
                continue
            try:
                login_dt = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
                if login_dt < cutoff:
                    stale.append(u)
            except (ValueError, TypeError):
                stale.append(u)

        failures = [
            FailingResource(
                resource_type="user",
                resource_identifier=u.get("email", u.get("id", "unknown")),
                details={
                    "user_id": u.get("id"),
                    "status": u.get("status"),
                    "last_login": u.get("last_login"),
                },
            )
            for u in stale
        ]

        evidence = {
            "total_users": len(users),
            "active_users": len(active_users),
            "stale_users": len(stale),
            "threshold_days": threshold_days,
            "cutoff_date": cutoff.isoformat(),
            "stale_user_emails": [u.get("email") for u in stale],
        }

        if stale:
            return EvaluationResult(
                status="fail",
                summary=f"{len(stale)} active users have not logged in for over {threshold_days} days",
                evidence=evidence,
                failures=failures,
                metadata={"evaluator": "no_inactive_users"},
            )

        return EvaluationResult(
            status="pass",
            summary=f"All {len(active_users)} active users have logged in within the last {threshold_days} days",
            evidence=evidence,
            metadata={"evaluator": "no_inactive_users"},
        )
