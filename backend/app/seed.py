"""Seed the database with initial control definitions.

Run directly: python -m app.seed
Idempotent: skips controls that already exist (matched by key).
"""
import logging

from app.database import SessionLocal
from app.models import Control, ControlCurrentState

logger = logging.getLogger("panopticon.seed")

CONTROLS = [
    {
        "key": "mfa_enforced",
        "name": "MFA Enforced for All Active Users",
        "description": "Verifies that every active user in the identity provider has MFA enrolled. Flags users with active status but no MFA factors configured.",
        "owner": "Security Engineering",
        "connector_type": "okta",
        "evaluator_type": "mfa_enforced",
        "config_json": {},
    },
    {
        "key": "no_inactive_users",
        "name": "No Stale Inactive Users",
        "description": "Checks that no active users have been inactive beyond the configured threshold. Identifies accounts that should be deprovisioned or reviewed.",
        "owner": "IT Operations",
        "connector_type": "okta",
        "evaluator_type": "no_inactive_users",
        "config_json": {"inactivity_threshold_days": 90},
    },
    {
        "key": "branch_protection",
        "name": "Branch Protection on Critical Repos",
        "description": "Verifies that all configured critical repositories have branch protection enabled on their default branch, including required reviews.",
        "owner": "Platform Engineering",
        "connector_type": "github",
        "evaluator_type": "branch_protection",
        "config_json": {"critical_repos": ["org/api-service", "org/web-app", "org/infra-config"]},
    },
    {
        "key": "no_direct_push",
        "name": "No Direct Push to Main",
        "description": "Verifies that direct pushes to the default branch are blocked on all critical repositories. Ensures all changes go through pull requests.",
        "owner": "Platform Engineering",
        "connector_type": "github",
        "evaluator_type": "no_direct_push",
        "config_json": {"critical_repos": ["org/api-service", "org/web-app", "org/infra-config"]},
    },
    {
        "key": "audit_logging",
        "name": "Cloud Audit Logging Enabled",
        "description": "Verifies that CloudTrail is enabled and actively logging in all configured production AWS accounts.",
        "owner": "Cloud Security",
        "connector_type": "aws",
        "evaluator_type": "audit_logging",
        "config_json": {"production_accounts": ["123456789012", "234567890123"]},
    },
]


def seed_controls() -> None:
    db = SessionLocal()
    try:
        for ctrl_data in CONTROLS:
            existing = db.query(Control).filter(Control.key == ctrl_data["key"]).first()
            if existing:
                logger.info(f"Control '{ctrl_data['key']}' already exists, skipping")
                continue

            control = Control(**ctrl_data)
            db.add(control)
            db.flush()

            state = ControlCurrentState(control_id=control.id, current_status="pending")
            db.add(state)

            logger.info(f"Seeded control: {ctrl_data['key']}")

        db.commit()
        logger.info("Seed complete")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_controls()
