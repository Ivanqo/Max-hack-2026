# UniPath MAX

UniPath MAX is an MVP student career platform with a Django REST backend, a React student app, a React admin app, PostgreSQL, deterministic matching, Career GPS, verified knowledge search, analytics, and a bounded MAX notification adapter.

## Architecture

```text
React Student UI ---\
                    +--> Django REST API --> PostgreSQL
React Admin UI -----/          |
                               +--> Matching Engine
                               +--> Career GPS
                               +--> Knowledge Search
                               +--> Analytics
                               +--> MAX Integration Adapter
```

The project is a modular monolith: one backend process owns the product workflows, while domain modules keep accounts, profiles, careers, opportunities, knowledge, analytics, subscriptions, notifications, and universities separate.

## Structure

```text
backend/            Django REST API and domain services
frontend-student/   Student React app
frontend-admin/     Admin React app
docs/               Architecture notes
docker-compose.yml  PostgreSQL, backend, and both frontends
.env.example        Environment template
```

## Requirements

- Docker and Docker Compose for the full stack.
- Node.js 20+ for local frontend work.
- Python 3.12+ and PostgreSQL for local backend work. SQLite is supported for quick local tests with `DB_ENGINE=sqlite`.

## Quick Start With Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

Open:

- Student app: http://localhost:3000
- Admin app: http://localhost:3001
- Backend API: http://localhost:8000/api/health/

## Local Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt
set DB_ENGINE=sqlite
./.venv/Scripts/python manage.py migrate
./.venv/Scripts/python manage.py seed_demo
./.venv/Scripts/python manage.py runserver
```

On PowerShell use `$env:DB_ENGINE='sqlite'` instead of `set DB_ENGINE=sqlite`.

## Local Frontends

```bash
cd frontend-student
npm install
npm run dev
```

```bash
cd frontend-admin
npm install
npm run dev
```

## Environment

Core variables are listed in `.env.example`:

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL` or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CORS_ALLOWED_ORIGINS`
- `VITE_API_URL`
- `MAX_API_URL`, `MAX_BOT_TOKEN`, `MAX_INTEGRATION_MODE`

`MAX_INTEGRATION_MODE=mock` keeps notifications inside the product as simulated messages. Use `real` only when a real MAX endpoint and bot token are configured.

## Demo Users

All demo users use password `demo12345`.

- Admin: `admin@demo.local`
- Editor: `editor@demo.local`
- Student: `student@demo.local`
- Second tenant student: `student@north.local`

## Tests

```bash
cd backend
set DB_ENGINE=sqlite
./.venv/Scripts/python -c "import os, pytest; os.environ['DB_ENGINE']='sqlite'; raise SystemExit(pytest.main())"
```

```bash
cd frontend-student
npm run test
npm run build
```

```bash
cd frontend-admin
npm run test
npm run build
```

## API Overview

- `POST /api/auth/login/`, `POST /api/auth/register/`, `GET /api/auth/profile/`
- `GET /api/universities`, `GET /api/institutes`, `GET /api/interests`, `POST /api/onboarding`
- `GET /api/student/career-gps`, `GET /api/career/goals`, `GET /api/career/analysis/<id>`
- `GET /api/student/opportunities`, `POST|DELETE /api/student/opportunities/<id>/save`
- `GET|POST /api/student/subscriptions`
- `GET /api/knowledge/search`
- `GET|POST /api/admin/opportunities`, `GET|PATCH|DELETE /api/admin/opportunities/<id>`
- `GET|POST /api/admin/knowledge`, `GET|PATCH|DELETE /api/admin/knowledge/<id>`
- `GET|POST /api/admin/career-roles`, `GET|PATCH|DELETE /api/admin/career-roles/<id>`
- `GET /api/admin/analytics`

## Matching

Opportunity matching is deterministic. The service compares student profile interests, skills, course, and career goal with opportunity type, title, description, audience, and required skills. Results include a percentage, reasons, and skill gaps.

## Career GPS

Career GPS compares the student's confirmed skills with a target career role. It returns readiness score, strengths, gaps, and next actions that are readable enough for a student UI and stable enough for tests.

## MVP Limits

- Knowledge search is deterministic keyword matching, not semantic retrieval.
- MAX delivery defaults to mock mode; real delivery is isolated behind an adapter.
- Demo institutes/programs are static MVP reference data.
- Multi-tenant isolation is implemented by university fields and tested for key student flows, but it is not a full enterprise tenant system yet.
