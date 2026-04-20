# PANOPTICON

Security control monitoring service. Continuously evaluates critical security and compliance controls across Okta, GitHub, and AWS, producing deterministic pass/fail results with evidence snapshots and Slack alerts on drift.

## Controls

| Control | Connector | What it checks |
|---------|-----------|----------------|
| MFA Enforced | Okta | All active users have MFA enrolled |
| No Inactive Users | Okta | No active users inactive beyond threshold |
| Branch Protection | GitHub | Critical repos have branch protection enabled |
| No Direct Push | GitHub | Critical repos block direct pushes to main |
| Audit Logging | AWS | CloudTrail enabled in production accounts |

## Quick Start

```bash
# 1. Copy env file and configure
cp .env.example .env
# Edit .env with your connector credentials

# 2. Start everything
docker compose up

# 3. Open
# Dashboard: http://localhost:3000
# API:       http://localhost:8000/api/health
# Docs:      http://localhost:8000/docs
```

The scheduler runs all controls on startup and then every 6 hours (configurable via `DEFAULT_CADENCE_SECONDS`).

## Development

**Backend only:**
```bash
cd backend
pip install -r requirements.txt
# Start Postgres separately or use: docker compose up db
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

**Frontend only:**
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service health + scheduler status |
| GET | `/api/controls` | List controls with current state |
| GET | `/api/controls/{id}` | Control detail |
| GET | `/api/controls/{id}/runs` | Run history |
| GET | `/api/controls/{id}/runs/latest` | Latest run with evidence + failures |
| POST | `/api/controls/{id}/run` | Trigger ad-hoc run |
| GET | `/api/runs/{id}` | Single run detail |
| GET | `/api/failures` | All currently failing resources |

## Architecture

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler
- **Database:** Postgres 16
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Containerized:** Docker Compose

Connectors fetch data from external systems. Evaluators are pure deterministic functions that take data and return pass/fail with evidence. The scheduler runs evaluations on a fixed cadence. Alerts fire on status transitions to Slack.
