from __future__ import annotations

from app.evaluators.base import EvaluatorBase, EvaluationResult, FailingResource


class NoDirectPushEvaluator(EvaluatorBase):
    """Check that direct pushes to default branch are blocked on all critical repos.

    Uses the same connector data as branch_protection. Specifically checks
    that push restrictions are in place (restrictions != null in GitHub API).

    Expected data from connector:
    {
        "repos": [
            {
                "full_name": "org/repo",
                "default_branch": "main",
                "branch_protection": {
                    "enabled": true,
                    "restrict_pushes": true,
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

        non_compliant = []
        for repo in repos:
            prot = repo.get("branch_protection")
            if prot is None or not prot.get("restrict_pushes"):
                non_compliant.append(repo)

        failures = [
            FailingResource(
                resource_type="repository",
                resource_identifier=r["full_name"],
                details={
                    "default_branch": r.get("default_branch"),
                    "has_protection": r.get("branch_protection") is not None,
                    "restrict_pushes": r["branch_protection"].get("restrict_pushes", False) if r.get("branch_protection") else False,
                    "error": r.get("error"),
                },
            )
            for r in non_compliant
        ]

        evidence = {
            "total_repos": len(repos),
            "compliant": len(repos) - len(non_compliant),
            "non_compliant": len(non_compliant),
            "non_compliant_repos": [r["full_name"] for r in non_compliant],
            "repo_details": [
                {
                    "full_name": r["full_name"],
                    "default_branch": r.get("default_branch"),
                    "has_protection": r.get("branch_protection") is not None,
                    "restrict_pushes": r["branch_protection"].get("restrict_pushes", False) if r.get("branch_protection") else False,
                }
                for r in repos
            ],
        }

        if non_compliant:
            return EvaluationResult(
                status="fail",
                summary=f"{len(non_compliant)} of {len(repos)} critical repos allow direct pushes to default branch",
                evidence=evidence,
                failures=failures,
                metadata={"evaluator": "no_direct_push"},
            )

        return EvaluationResult(
            status="pass",
            summary=f"All {len(repos)} critical repos block direct pushes to default branch",
            evidence=evidence,
            metadata={"evaluator": "no_direct_push"},
        )
