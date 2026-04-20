from app.evaluators.no_direct_push import NoDirectPushEvaluator

evaluator = NoDirectPushEvaluator()


def make_repo(name, has_protection=True, restrict_pushes=True):
    if not has_protection:
        return {"full_name": name, "default_branch": "main", "branch_protection": None}
    return {
        "full_name": name,
        "default_branch": "main",
        "branch_protection": {
            "enabled": True,
            "required_reviews": 1,
            "restrict_pushes": restrict_pushes,
        },
    }


def test_all_restricted():
    data = {"repos": [make_repo("org/a"), make_repo("org/b")]}
    r = evaluator.evaluate(data, {})
    assert r.status == "pass"
    assert len(r.failures) == 0


def test_unrestricted_push_fails():
    data = {"repos": [
        make_repo("org/a"),
        make_repo("org/b", restrict_pushes=False),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 1
    assert r.failures[0].resource_identifier == "org/b"


def test_no_protection_also_fails():
    data = {"repos": [make_repo("org/a", has_protection=False)]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert r.failures[0].resource_identifier == "org/a"


def test_mixed_failures():
    data = {"repos": [
        make_repo("org/ok"),
        make_repo("org/no-restrict", restrict_pushes=False),
        make_repo("org/no-prot", has_protection=False),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 2
    ids = {f.resource_identifier for f in r.failures}
    assert ids == {"org/no-restrict", "org/no-prot"}


def test_no_data_returns_error():
    r = evaluator.evaluate({}, {})
    assert r.status == "error"


def test_evidence_details():
    data = {"repos": [make_repo("org/a"), make_repo("org/b", restrict_pushes=False)]}
    r = evaluator.evaluate(data, {})
    assert r.evidence["total_repos"] == 2
    assert r.evidence["compliant"] == 1
    assert r.evidence["non_compliant"] == 1
