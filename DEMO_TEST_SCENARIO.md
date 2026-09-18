# UniPath MAX demo and real MAX test scenario

## 1. Local demo with seeded data

Use this path when you want a deterministic demo without real MAX delivery.

### Start from clean demo data

```powershell
cd D:\Proga\max-hack
copy .env.example .env
docker compose down -v
docker compose up --build -d
docker compose ps
```

Expected services:

- `max-hack-db` healthy
- `max-hack-backend` healthy
- `max-hack-frontend-student` healthy
- `max-hack-frontend-admin` healthy

Default URLs:

- Student app: `http://localhost:3000`
- Admin app: `http://localhost:3001`
- Backend health: `http://localhost:8000/api/health/`

If ports are occupied, set overrides in `.env` before startup:

```env
BACKEND_PORT=18000
STUDENT_PORT=13000
ADMIN_PORT=13001
```

Then use:

- Student app: `http://localhost:13000`
- Admin app: `http://localhost:13001`
- Backend health: `http://localhost:18000/api/health/`

### Run executable API smoke

Default port:

```powershell
D:\Proga\max-hack\backend\.venv\Scripts\python.exe D:\Proga\max-hack\backend\scripts\smoke_data_api.py --base-url http://localhost:8000
```

Port override example:

```powershell
D:\Proga\max-hack\backend\.venv\Scripts\python.exe D:\Proga\max-hack\backend\scripts\smoke_data_api.py --base-url http://localhost:18000
```

Expected result:

```text
PASS: DATA-API smoke scenario completed, including simulated notification dedupe.
```

The smoke checks:

- health
- student login
- blocked admin self-registration
- onboarding
- Career GPS
- opportunities with explainable match
- save opportunity
- subscription creation
- admin login
- admin publishes matching opportunity
- notification is created once
- repeated publish does not duplicate notification
- knowledge verified source
- knowledge fallback
- admin analytics

### Manual product demo

Demo accounts:

- Student: `student@demo.local / demo12345`
- Admin: `admin@demo.local / demo12345`
- Editor: `editor@demo.local / demo12345`

Steps:

1. Open Student app.
2. Log in as `student@demo.local`.
3. Open Profile or Onboarding and confirm:
   - university is set;
   - interests include Backend or internships;
   - skills include Python, Django, REST or SQL;
   - career goal is Backend Developer.
4. Open Career GPS and show:
   - readiness score;
   - strengths;
   - gaps;
   - next actions.
5. Open Opportunities and show:
   - match percentage;
   - match reasons;
   - gaps;
   - save action.
6. Create a subscription topic, for example `Backend`.
7. Open Admin app in another browser/session.
8. Log in as `admin@demo.local`.
9. Create and publish an active opportunity:
   - title: `Backend MAX Bot Internship`
   - type: `internship`
   - company: `MAX Labs`
   - requirements: `Python`, `Django`, `REST`
   - status: `active`
10. Return to student context and verify a notification exists.
11. In mock mode, delivery status must be `simulated`.
12. Search Knowledge for `практика` and show verified source.
13. Search Knowledge for a nonsense query and show fallback with escalation.

## 2. Real MAX test after bot token is connected

Use this path only when you have:

- real `MAX_BOT_TOKEN`;
- public HTTPS frontend URL for the mini app;
- public HTTPS backend URL for webhook/API;
- MAX bot or mini app entry configured by organizers/platform;
- bot username/link for `MAX_OPEN_APP_TARGET`.

### Configure production-like env

Edit `.env`.

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<strong-secret>
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,<public-backend-host>
CORS_ALLOWED_ORIGINS=https://<public-frontend-host>

MAX_API_URL=https://platform-api2.max.ru
MAX_INTEGRATION_MODE=real
MAX_BOT_TOKEN=<real-token>
MAX_WEBHOOK_SECRET=<random-32-plus-chars>
MAX_WEBHOOK_URL=https://<public-backend-host>/api/max/webhook/
MAX_OPEN_APP_TARGET=https://max.ru/<bot_username>
MAX_WEBAPP_BASE_URL=https://<public-frontend-host>/
AUTO_SEED_DEMO=true
```

If the frontend calls the API through the same public origin and reverse proxy, `VITE_API_URL=/api` is fine. If the frontend must call a separate backend origin, set `VITE_API_URL=https://<public-backend-host>/api` and rebuild the frontend containers.

### Start stack

```powershell
cd D:\Proga\max-hack
docker compose down
docker compose up --build -d
docker compose ps
```

Check health:

```powershell
curl https://<public-backend-host>/api/health/
```

Expected:

```json
{"status":"ok"}
```

### Register webhook

```powershell
docker compose exec backend python manage.py register_max_webhook
```

Expected:

```text
MAX webhook subscription registered.
```

If this fails, do not claim real MAX delivery. Fix token, webhook URL, HTTPS, or secret configuration first.

### Link a student to MAX identity

The notification can be delivered only to a user that has `max_user_id`.

Recommended real test path:

1. Open the bot in MAX.
2. Open the UniPath MAX mini app from the bot.
3. Let the mini app call `/api/max/launch/` with MAX launch data.
4. Complete onboarding in that MAX-launched student account.
5. Set skills:
   - Python level 4
   - Django level 3
   - REST level 3
6. Set career goal: `Backend Developer`.
7. Create subscription topic: `Backend`.

### Trigger real notification

1. Open Admin app.
2. Log in as `admin@demo.local / demo12345`.
3. Publish a matching opportunity:
   - title: `Backend MAX Real Delivery Test`
   - company: `MAX Labs`
   - type: `internship`
   - requirements: `Python`, `Django`, `REST`, `Backend`
   - status: `active`
4. Watch the MAX chat for a bot message.
5. Click the open app button.
6. Confirm the mini app opens and the relevant opportunity is visible.

### Verify through API

Use the linked student token from the mini app session, or inspect through admin/API if available.

Expected notification result for real mode:

- one notification for the new opportunity;
- no duplicate after re-saving or re-publishing the same opportunity;
- `delivery_status=sent`;
- `provider=max`;
- `provider_message_id` is present when MAX returns one.

If delivery fails, expected honest state is:

- `delivery_status=failed`;
- `last_error` is sanitized;
- product still works without pretending delivery succeeded.

## 3. What to record for presentation

Record these screenshots or short clips:

1. MAX bot opens mini app.
2. Student onboarding/profile with career goal and skills.
3. Career GPS with readiness and gaps.
4. Opportunities with match reasons and gaps.
5. Student subscription.
6. Admin creates/publishes opportunity.
7. MAX notification arrives.
8. Open app button returns to opportunity.
9. DATA-API smoke PASS.
10. Docker services healthy.

## 4. When to claim the MAX platform bonus

Claim the bonus only if all are true:

- real token was used;
- webhook was registered on public HTTPS;
- student was linked to `max_user_id`;
- admin publish created one notification;
- MAX message arrived in the real chat;
- open app action returned the user to the mini app;
- the scenario can be repeated for judges.

If any item is missing, present it as implemented integration boundary plus verified local mock mode, not as a completed real MAX bonus.

