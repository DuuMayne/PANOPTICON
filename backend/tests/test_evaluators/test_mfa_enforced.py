from app.evaluators.mfa_enforced import MfaEnforcedEvaluator


def make_user(email, status="ACTIVE", mfa_enrolled=True, factors=None):
    return {
        "id": email.split("@")[0],
        "email": email,
        "status": status,
        "mfa_enrolled": mfa_enrolled,
        "mfa_factors": factors or (["okta_verify"] if mfa_enrolled else []),
    }


evaluator = MfaEnforcedEvaluator()


def test_all_compliant():
    data = {"users": [make_user("a@x.com"), make_user("b@x.com")]}
    r = evaluator.evaluate(data, {})
    assert r.status == "pass"
    assert len(r.failures) == 0
    assert r.evidence["mfa_non_compliant"] == 0


def test_some_non_compliant():
    data = {"users": [
        make_user("a@x.com"),
        make_user("b@x.com", mfa_enrolled=False),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 1
    assert r.failures[0].resource_identifier == "b@x.com"


def test_deprovisioned_users_ignored():
    data = {"users": [
        make_user("active@x.com"),
        make_user("gone@x.com", status="DEPROVISIONED", mfa_enrolled=False),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "pass"
    assert len(r.failures) == 0


def test_no_users_returns_error():
    r = evaluator.evaluate({}, {})
    assert r.status == "error"


def test_empty_users_returns_error():
    r = evaluator.evaluate({"users": []}, {})
    assert r.status == "error"


def test_evidence_includes_rates():
    data = {"users": [
        make_user("a@x.com"),
        make_user("b@x.com", mfa_enrolled=False),
        make_user("c@x.com"),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.evidence["active_users"] == 3
    assert r.evidence["mfa_compliant"] == 2
    assert r.evidence["compliance_rate"] == round(2 / 3, 4)
