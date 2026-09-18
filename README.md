# UniPath MAX

UniPath MAX is a reproducible MVP for the educational solutions track: a MAX mini-app plus Django API that helps students build a career profile, get Career GPS guidance, match opportunities, subscribe to topics, and receive proactive MAX bot notifications when an admin publishes a relevant opportunity.

## Main Demo Scenario

1. Student opens the MAX bot.
2. Bot opens the MAX mini-app.
3. Mini-app sends MAX `initData` to `POST /api/max/launch/`.
4. Backend validates signed WebAppData, links `max_user_id` to a local student, and returns JWT tokens.
5. Student completes onboarding with university, institute, program, study year, interests, skills, and career goal.
6. Career GPS and opportunity matching are calculated from saved profile and `StudentSkill` rows.
7. Student saves an opportunity and creates a subscription.
8. Admin publishes a matching opportunity.
9. Backend creates one idempotent notification per matching subscription.
10. In `mock` mode the notification is stored as `simulated`; in `real` mode `RealMaxClient` sends `POST https://platform-api2.max.ru/messages?user_id=<max_user_id>` with `Authorization: <MAX_BOT_TOKEN>`.
11. If `MAX_OPEN_APP_TARGET` is configured, the MAX message includes an `open_app` inline button with payload `opportunity_<id>`.
12. User returns to the opportunity list and sees match score, reasons, and gaps.

## Architecture

```text
MAX Bot
  -> MAX mini-app / React Student UI
      -> Django REST API
          -> PostgreSQL
          -> Career GPS
          -> Opportunity Matching
          -> Subscriptions
          -> Notifications
          -> MAX Bot API

React Admin UI -> Django REST API
```

The backend is a modular Django monolith with separate apps for accounts, profiles, careers, opportunities, subscriptions, notifications, analytics, knowledge, and universities.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The backend container runs migrations and, by default, an idempotent demo seed (`AUTO_SEED_DEMO=true`). To disable demo seed, set `AUTO_SEED_DEMO=false`.

Open:

- Student app: http://localhost:3000
- Admin app: http://localhost:3001
- Backend health: http://localhost:8000/api/health/
- OpenAPI contract: `openapi.yaml`
- Contest API checks: `DATA-API.yaml`

## Environment Variables

Core:

```env
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
DATABASE_URL=postgresql://maxhack_user:changeme123@db:5432/maxhack
VITE_API_URL=/api
AUTO_SEED_DEMO=true
```

MAX local/demo:

```env
MAX_API_URL=https://platform-api2.max.ru
MAX_INTEGRATION_MODE=mock
MAX_BOT_TOKEN=
MAX_WEBHOOK_SECRET=
MAX_WEBHOOK_URL=
MAX_OPEN_APP_TARGET=
MAX_WEBAPP_BASE_URL=http://localhost:3000
MAX_INITDATA_MAX_AGE_SECONDS=3600
```

MAX production:

```env
MAX_API_URL=https://platform-api2.max.ru
MAX_BOT_TOKEN=<real bot token>
MAX_INTEGRATION_MODE=real
MAX_WEBHOOK_SECRET=<random 32+ chars>
MAX_WEBHOOK_URL=https://<public-domain>/api/max/webhook/
MAX_OPEN_APP_TARGET=https://max.ru/<bot_username>
MAX_WEBAPP_BASE_URL=https://<public-domain>/
```

Do not put real secrets in frontend code, `.env.example`, README, screenshots, or commits.

## Ports

- `5432`: PostgreSQL
- `8000`: Django API (`BACKEND_PORT` can override)
- `3000`: Student frontend (`STUDENT_PORT` can override)
- `3001`: Admin frontend (`ADMIN_PORT` can override)

## Demo Accounts

All seeded demo users use password `demo12345`.

- Admin: `admin@demo.local`
- Editor: `editor@demo.local`
- Student: `student@demo.local`
- Second tenant student: `student@north.local`

## Test Data

`python manage.py seed_demo` creates synthetic universities, users, career roles, skills, opportunities, knowledge items, subscriptions, and tenant-isolation marker data. The data is model/demo data, not live university data.

## MAX Integration

Real API base: `https://platform-api2.max.ru`.

Implemented production contract:

- Message send: `POST /messages?user_id=<max_user_id>`
- Authorization: raw header `Authorization: <MAX_BOT_TOKEN>`
- Webhook receiver: `POST /api/max/webhook/`
- Webhook protection: `X-Max-Bot-Api-Secret`
- Webhook subscription registration: `python manage.py register_max_webhook`
- Mini-app launch validation: `POST /api/max/launch/` validates signed WebAppData/initData and links `max_user_id`.
- `open_app` return buttons use `MAX_OPEN_APP_TARGET`, the public MAX bot username/link for the mini-app. `MAX_WEBAPP_BASE_URL` is the public frontend URL used when configuring the mini-app itself.

Local deterministic mode:

- `MAX_INTEGRATION_MODE=mock`
- Notifications are created and marked `delivery_status=simulated`
- No real MAX network call is made

## Manual Smoke Check

Executable check:

```bash
cd backend
python scripts/smoke_data_api.py --base-url http://localhost:8000
```

On Windows with the local virtualenv:

```powershell
backend/.venv/Scripts/python.exe backend/scripts/smoke_data_api.py --base-url http://localhost:8000
```

The smoke runner follows `DATA-API.yaml`: health, login, onboarding, Career GPS, opportunities, save, subscription, admin publish, notification verification, idempotent republish, knowledge verified source/fallback, and admin analytics.

1. Start stack with `docker compose up --build`.
2. Open student app and login as `student@demo.local / demo12345`.
3. Complete onboarding or update `/profile` skills.
4. Open Career GPS and verify readiness/gaps reflect selected skills.
5. Open Opportunities, save one item, create subscription topic `Backend`.
6. Open admin app and login as `admin@demo.local / demo12345`.
7. Create an active opportunity with requirements `Python`, `Django`, `REST`.
8. Verify backend creates one notification for the matching subscription.
9. In mock mode, notification has `delivery_status=simulated`.
10. In real mode, linked students receive a MAX message with an `open_app` button returning to `opportunity_<id>` when `MAX_OPEN_APP_TARGET` points to the public MAX bot/mini-app.

Expected result: the student can return to the opportunity and see match percentage, reasons, gaps, and save state without manual DB edits.

## API

The documented scenario API lives in `openapi.yaml`. The contest check file is `DATA-API.yaml`.

Most-used endpoints:

- `POST /api/auth/login/`
- `POST /api/auth/register/`
- `POST /api/max/launch/`
- `POST /api/max/webhook/`
- `POST /api/onboarding`
- `GET /api/student/profile`
- `GET /api/student/career-gps`
- `GET /api/student/opportunities`
- `GET /api/student/opportunities/{id}`
- `POST /api/student/opportunities/{id}/save`
- `GET|POST /api/student/subscriptions`
- `GET /api/v1/notifications/`
- `GET /api/knowledge/search?q=...`
- `GET|POST /api/admin/opportunities`
- `GET /api/admin/analytics`

## Tests

Backend:

```bash
cd backend
set DB_ENGINE=sqlite
python -m pytest
```

Frontend:

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

Operational commands:

```bash
python manage.py retry_failed_notifications --limit 100
python manage.py register_max_webhook
```

## Security Notes

- Public registration only creates student accounts and rejects privileged roles.
- MAX bot token is read only by backend.
- Webhook requests are protected by `X-Max-Bot-Api-Secret`.
- Notification delivery state, read state, provider message id, timestamps, and idempotency key are stored separately.
- Duplicate publish/webhook events do not create duplicate notification records.
- See `SECURITY.md` for secret handling and scan commands.

## Known Limitations

- `mock` MAX mode is deterministic local simulation, not proof of production delivery.
- Real MAX return buttons require a public MAX bot/mini-app target in `MAX_OPEN_APP_TARGET`; local frontend URLs are not a valid proof of production return flow.
- Knowledge search is deterministic keyword matching over seeded verified records.
- Demo data is synthetic.
- JWT refresh is present in backend but not fully wired into frontend UX.
- Production deployment must provide public HTTPS, strict allowed hosts/CORS, and real MAX bot settings.
