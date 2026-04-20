from __future__ import annotations

from app.evaluators.base import EvaluatorBase, EvaluationResult, FailingResource


class BranchProtectionEvaluator(EvaluatorBase):
    """Check that all critical repos have branch protection enabled on default branch.

    Expected data from connector:
    {
        "repos": [
            {
                "full_name": "org/repo",
                "default_branch": "main",
                "branch_protection": {
                    "enabled": true,
                    "required_reviews": 1,
                    "enforce_admins": true,
                    ...
                } | null
            }
        ]
    }
    """

    def evaluate(self, data: dict, config: dict) -> EvaluationResult:
        repos = data.get("repos", [])
        if not repos:
            return EvaluationResult(
                status="error",
                summary="No repository data returned from connector",
                metadata={"repo_count": 0},
            )

        unprotected = []
        for repo in repos:
            prot = repo.get("branch_protection")
            if prot is None or not prot.get("enabled"):
                unprotected.append(repo)

        failures = [
            FailingResource(
                resource_type="repository",
                resource_identifier=r["full_name"],
                details={
                    "default_branch": r.get("default_branch"),
                    "branch_protection": r.get("branch_protection"),
                    "error": r.get("error"),
                },
            )
            for r in unprotected
        ]

        evidence = {
            "total_repos": len(repos),
            "protected": len(repos) - len(unprotected),
            "unprotected": len(unprotected),
            "unprotected_repos": [r["full_name"] for r in unprotected],
            "repo_details": [
                {
                    "full_name": r["full_name"],
                    "default_branch": r.get("default_branch"),
                    "has_protection": r.get("branch_protection") is not None and r["branch_protection"].get("enabled", False),
                    "required_reviews": r["branch_protection"].get("required_reviews", 0) if r.get("branch_protection") else 0,
                }
                for r in repos
            ],
        }

        if unprotected:
            return EvaluationResult(
                status="fail",
                summary=f"{len(unprotected)} of {len(repos)} critical repos lack branch protection on default branch",
                evidence=evidence,
                failures=failures,
                metadata={"evaluator": "branch_protection"},
            )

        return EvaluationResult(
            status="pass",
            summary=f"All {len(repos)} critical repos have branch protection enabled",
            evidence=evidence,
            metadata={"evaluator": "branch_protection"},
        )
