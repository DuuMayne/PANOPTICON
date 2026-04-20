from app.evaluators.base import EvaluatorBase, EvaluationResult, FailingResource


class MfaEnforcedEvaluator(EvaluatorBase):
    """Check that all active users have MFA enrolled.

    Expected data from connector:
    {
        "users": [
            {
                "id": "okta-user-id",
                "email": "user@example.com",
                "status": "ACTIVE",
                "mfa_enrolled": true,
                "mfa_factors": ["okta_verify", "sms"]
            },
            ...
        ]
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

        active_users = [u for u in users if u.get("status") == "ACTIVE"]
        non_compliant = [u for u in active_users if not u.get("mfa_enrolled")]

        failures = [
            FailingResource(
                resource_type="user",
                resource_identifier=u.get("email", u.get("id", "unknown")),
                details={
                    "user_id": u.get("id"),
                    "status": u.get("status"),
                    "mfa_enrolled": u.get("mfa_enrolled", False),
                    "mfa_factors": u.get("mfa_factors", []),
                },
            )
            for u in non_compliant
        ]

        total_active = len(active_users)
        compliant = total_active - len(non_compliant)

        evidence = {
            "total_users": len(users),
            "active_users": total_active,
            "mfa_compliant": compliant,
            "mfa_non_compliant": len(non_compliant),
            "compliance_rate": round(compliant / total_active, 4) if total_active > 0 else 0,
            "non_compliant_users": [u.get("email") for u in non_compliant],
        }

        if non_compliant:
            return EvaluationResult(
                status="fail",
                summary=f"{len(non_compliant)} of {total_active} active users do not have MFA enrolled",
                evidence=evidence,
                failures=failures,
                metadata={"evaluator": "mfa_enforced"},
            )

        return EvaluationResult(
            status="pass",
            summary=f"All {total_active} active users have MFA enrolled",
            evidence=evidence,
            metadata={"evaluator": "mfa_enforced"},
        )
