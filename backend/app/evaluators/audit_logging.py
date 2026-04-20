from __future__ import annotations

from app.evaluators.base import EvaluatorBase, EvaluationResult, FailingResource


class AuditLoggingEvaluator(EvaluatorBase):
    """Check that CloudTrail audit logging is enabled in all production accounts.

    Expected data from connector:
    {
        "accounts": [
            {
                "account_id": "123456789012",
                "account_name": "prod-us",
                "cloudtrail_enabled": true,
                "is_logging": true,
                "trail_name": "org-trail"
            }
        ]
    }
    """

    def evaluate(self, data: dict, config: dict) -> EvaluationResult:
        accounts = data.get("accounts", [])
        if not accounts:
            return EvaluationResult(
                status="error",
                summary="No account data returned from connector",
                metadata={"account_count": 0},
            )

        non_compliant = []
        for acct in accounts:
            if not acct.get("cloudtrail_enabled") or not acct.get("is_logging"):
                non_compliant.append(acct)

        failures = [
            FailingResource(
                resource_type="account",
                resource_identifier=a.get("account_id", "unknown"),
                details={
                    "account_name": a.get("account_name"),
                    "cloudtrail_enabled": a.get("cloudtrail_enabled", False),
                    "is_logging": a.get("is_logging", False),
                    "trail_name": a.get("trail_name"),
                    "error": a.get("error"),
                },
            )
            for a in non_compliant
        ]

        evidence = {
            "total_accounts": len(accounts),
            "compliant": len(accounts) - len(non_compliant),
            "non_compliant": len(non_compliant),
            "non_compliant_accounts": [a.get("account_id") for a in non_compliant],
            "account_details": [
                {
                    "account_id": a.get("account_id"),
                    "account_name": a.get("account_name"),
                    "cloudtrail_enabled": a.get("cloudtrail_enabled", False),
                    "is_logging": a.get("is_logging", False),
                    "trail_name": a.get("trail_name"),
                }
                for a in accounts
            ],
        }

        if non_compliant:
            return EvaluationResult(
                status="fail",
                summary=f"{len(non_compliant)} of {len(accounts)} production accounts lack active CloudTrail logging",
                evidence=evidence,
                failures=failures,
                metadata={"evaluator": "audit_logging"},
            )

        return EvaluationResult(
            status="pass",
            summary=f"All {len(accounts)} production accounts have CloudTrail logging enabled",
            evidence=evidence,
            metadata={"evaluator": "audit_logging"},
        )
