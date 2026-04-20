from app.evaluators.branch_protection import BranchProtectionEvaluator

evaluator = BranchProtectionEvaluator()


def make_repo(name, enabled=True, reviews=1, enforce_admins=True):
    if not enabled:
        return {"full_name": name, "default_branch": "main", "branch_protection": None}
    return {
        "full_name": name,
        "default_branch": "main",
        "branch_protection": {
            "enabled": True,
            "required_reviews": reviews,
            "enforce_admins": enforce_admins,
            "restrict_pushes": True,
        },
    }


def test_all_protected():
    data = {"repos": [make_repo("org/a"), make_repo("org/b")]}
    r = evaluator.evaluate(data, {})
    assert r.status == "pass"
    assert len(r.failures) == 0


def test_unprotected_repo_fails():
    data = {"repos": [make_repo("org/a"), make_repo("org/b", enabled=False)]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 1
    assert r.failures[0].resource_identifier == "org/b"


def test_all_unprotected():
    data = {"repos": [make_repo("org/a", enabled=False), make_repo("org/b", enabled=False)]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 2


def test_no_repos_returns_error():
    r = evaluator.evaluate({"repos": []}, {})
    assert r.status == "error"


def test_no_data_returns_error():
    r = evaluator.evaluate({}, {})
    assert r.status == "error"


def test_evidence_has_repo_details():
    data = {"repos": [make_repo("org/a"), make_repo("org/b", enabled=False)]}
    r = evaluator.evaluate(data, {})
    assert r.evidence["total_repos"] == 2
    assert r.evidence["protected"] == 1
    assert r.evidence["unprotected"] == 1
    assert "org/b" in r.evidence["unprotected_repos"]
