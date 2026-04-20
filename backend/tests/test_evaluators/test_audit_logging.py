from app.evaluators.audit_logging import AuditLoggingEvaluator

evaluator = AuditLoggingEvaluator()


def make_account(account_id, enabled=True, logging=True):
    return {
        "account_id": account_id,
        "account_name": f"acct-{account_id}",
        "cloudtrail_enabled": enabled,
        "is_logging": logging,
        "trail_name": "org-trail" if enabled else None,
    }


def test_all_compliant():
    data = {"accounts": [make_account("111"), make_account("222")]}
    r = evaluator.evaluate(data, {})
    assert r.status == "pass"
    assert len(r.failures) == 0


def test_not_logging_fails():
    data = {"accounts": [
        make_account("111"),
        make_account("222", enabled=True, logging=False),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 1
    assert r.failures[0].resource_identifier == "222"


def test_no_trail_fails():
    data = {"accounts": [make_account("111", enabled=False, logging=False)]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert r.failures[0].resource_identifier == "111"


def test_multiple_failures():
    data = {"accounts": [
        make_account("111", enabled=False, logging=False),
        make_account("222", enabled=True, logging=False),
        make_account("333"),
    ]}
    r = evaluator.evaluate(data, {})
    assert r.status == "fail"
    assert len(r.failures) == 2


def test_no_data_returns_error():
    r = evaluator.evaluate({}, {})
    assert r.status == "error"


def test_empty_accounts_returns_error():
    r = evaluator.evaluate({"accounts": []}, {})
    assert r.status == "error"


def test_evidence_details():
    data = {"accounts": [make_account("111"), make_account("222", logging=False)]}
    r = evaluator.evaluate(data, {})
    assert r.evidence["total_accounts"] == 2
    assert r.evidence["compliant"] == 1
    assert r.evidence["non_compliant"] == 1
    assert "222" in r.evidence["non_compliant_accounts"]
