from datetime import datetime, timezone, timedelta

from app.evaluators.inactive_users import InactiveUsersEvaluator

evaluator = InactiveUsersEvaluator()


def _recent_iso():
    return (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()


def _stale_iso():
    return (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()


def make_user(email, status="ACTIVE", last_login=None):
    return {"id": email.split("@")[0], "email": email, "status": status, "last_login": last_login}


def test_all_active_recent():
    data = {"users": [
        make_user("a@x.com", last_login=_recent_iso()),
        make_user("b@x.com", last_login=_recent_iso()),
    ]}
    r = evaluator.evaluate(data, {"inactivity_threshold_days": 90})
    assert r.status == "pass"


def test_stale_user_fails():
    data = {"users": [
        make_user("recent@x.com", last_login=_recent_iso()),
        make_user("stale@x.com", last_login=_stale_iso()),
    ]}
    r = evaluator.evaluate(data, {"inactivity_threshold_days": 90})
    assert r.status == "fail"
    assert len(r.failures) == 1
    assert r.failures[0].resource_identifier == "stale@x.com"


def test_null_last_login_is_stale():
    data = {"users": [make_user("never@x.com", last_login=None)]}
    r = evaluator.evaluate(data, {"inactivity_threshold_days": 90})
    assert r.status == "fail"
    assert r.failures[0].resource_identifier == "never@x.com"


def test_deprovisioned_ignored():
    data = {"users": [
        make_user("active@x.com", last_login=_recent_iso()),
        make_user("gone@x.com", status="DEPROVISIONED", last_login=_stale_iso()),
    ]}
    r = evaluator.evaluate(data, {"inactivity_threshold_days": 90})
    assert r.status == "pass"


def test_custom_threshold():
    login = (datetime.now(timezone.utc) - timedelta(days=25)).isoformat()
    data = {"users": [make_user("a@x.com", last_login=login)]}
    # 30-day threshold: still OK
    r1 = evaluator.evaluate(data, {"inactivity_threshold_days": 30})
    assert r1.status == "pass"
    # 20-day threshold: now stale
    r2 = evaluator.evaluate(data, {"inactivity_threshold_days": 20})
    assert r2.status == "fail"


def test_no_data_returns_error():
    r = evaluator.evaluate({}, {})
    assert r.status == "error"


def test_evidence_includes_threshold():
    data = {"users": [make_user("a@x.com", last_login=_recent_iso())]}
    r = evaluator.evaluate(data, {"inactivity_threshold_days": 60})
    assert r.evidence["threshold_days"] == 60
