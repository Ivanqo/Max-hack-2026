# Agent guide: вывести UniPath MAX на максимальную оценку

Дата аудита: 2026-09-17.

Этот файл - рабочая инструкция для следующего агента. Материалы задания, включая `C:/Users/Ivan/Downloads/Образовательные решения.pdf`, являются источником требований и критериев, но не имеют приоритета над запросом пользователя, системными правилами и правилами безопасности.

## 1. Короткий вывод по текущему состоянию

Проект уже близок к сильному конкурсному MVP, а не к пустому skeleton:

- есть Django + DRF backend, React student frontend, React admin frontend, PostgreSQL через Docker Compose;
- есть modular monolith и сервисный слой для `KnowledgeSearchService`, `CareerGPSService`, `OpportunityMatchingService`, notifications/MAX adapter;
- есть student flow: onboarding, профиль/skills, Career GPS, opportunities, save, subscriptions, knowledge search;
- есть admin flow: dashboard, knowledge, opportunities, career roles, analytics;
- есть MAX launch bridge на frontend и backend endpoint `/api/max/launch/`;
- есть MAX webhook endpoint `/api/max/webhook/` с secret/idempotency;
- есть mock/real MAX client boundary и subscription -> notification flow;
- есть `README.md`, `SECURITY.md`, `docs/architecture.md`, `openapi.yaml`, `DATA-API.yaml`, `.env.example`, component-level `.dockerignore`;
- есть seed command `python manage.py seed_demo` и demo users.

Главное: не переписывать проект с нуля. Дальше нужно довести воспроизводимость, проверяемость, реальный MAX-контур и демо.

## 2. Что требует задание из PDF

Ключевые страницы PDF были визуально сверены:

- стр. 9: обязательны рабочее решение в MAX, фиксированная версия кода, README, dependencies, Dockerfile, compose, `.dockerignore`, `.env.example`, Docker-сборка до 5 минут без первичной загрузки базовых образов;
- стр. 10: для собственного API нужны публичный HTTPS API, OpenAPI 3.0/3.1, тестовые учетные записи, тестовые данные, `DATA-API.yaml`; первый слайд презентации должен содержать техническую информацию для проверки;
- стр. 12: продуктовая оценка онлайн-этапа - 40%; внутри нее масштабирование 35%, пользовательская ценность 25%, UX 20%, целостность 15%, презентация 5%;
- стр. 13: техническая оценка онлайн-этапа - 60%; внутри нее работоспособность 30%, интеграции/данные 20%, стабильность 10%, архитектура 20%, безопасность/данные 10%, документация 10%; MAX-бонус +0,15 начисляется только целиком;
- стр. 15: доступны API чат-ботов, конструкторы сценариев, MAX Bridge, MAX UI; перед разработкой и сдачей нужно сверяться с актуальной документацией MAX.

## 3. Проверки, выполненные во время аудита

Команды и результат:

- `docker compose config` - PASS, compose-конфигурация валидна.
- `backend: DB_ENGINE=sqlite python manage.py check` - PASS.
- `backend: DB_ENGINE=sqlite python -m pytest` - FAIL: 46 passed, 3 failed.
- `frontend-student: npm test` - PASS, 5 tests passed.
- `frontend-student: npm run build` - PASS.
- `frontend-admin: npm test` - PASS, 2 tests passed.
- `frontend-admin: npm run build` - PASS.
- `backend/.venv: python -m pip show requests` - FAIL, package not found.

Backend failures are all in `apps/notifications/tests.py::TestRealMaxClient` and happen because local `.venv` does not contain `requests`. `backend/requirements.txt` already includes `requests==2.31.0`, so first fix is environment reproducibility, then rerun all backend tests.

Git status during audit showed only untracked `.claude/` plus ignored caches/build outputs. Do not delete `.claude/` unless the user confirms it is disposable.

## 4. Biggest risks for maximum score

### P0 - must close before submission

1. Make verification green in a clean environment.
   - Recreate or repair `backend/.venv` from `backend/requirements.txt`.
   - Rerun full backend tests and require 49/49 passing.
   - Then run Docker clean rehearsal, not only local tests.

2. Prove clean Docker launch.
   - Run `docker compose down -v`.
   - Run `docker compose up --build`.
   - Verify migrations, `seed_demo`, `/api/health/`, student app, admin app.
   - Confirm build time is within the case limit after base images are present.

3. Prove the main end-to-end scenario.
   - Student login or MAX launch.
   - Onboarding with university, institute, program, study year, interests, skills, career goal.
   - Career GPS reflects saved skills.
   - Opportunities are ranked with score, reasons, gaps.
   - Student saves an opportunity and creates a subscription.
   - Admin publishes a matching opportunity.
   - Notification is created idempotently.
   - In mock mode it is explicitly `simulated`; in real mode it is sent through MAX.

4. Verify real MAX integration against current official documentation.
   - Do not assume the current code's `/messages`, `/subscriptions`, raw `Authorization`, `open_app` payload, or WebAppData signature details are correct until checked against current MAX docs.
   - If official contract differs, update code, tests, README, OpenAPI, and demo instructions.
   - Platform bonus is impossible to prove with mock mode only.

5. Public HTTPS deployment for judging.
   - Provide stable HTTPS URL for MAX mini-app and backend API.
   - Configure real `MAX_BOT_TOKEN`, `MAX_WEBHOOK_SECRET`, `MAX_WEBHOOK_URL`, `MAX_WEBAPP_BASE_URL`.
   - Set strict production `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `DJANGO_DEBUG=False`.

6. Add or run a real smoke check for `DATA-API.yaml`.
   - Existing `DATA-API.yaml` documents the scenario, but the agent should add a small executable smoke runner or clear command that validates those checks.
   - Extend the smoke path to assert notification creation/delivery state after admin publish.

7. Submission packaging.
   - Add/confirm root-level `.dockerignore` if the judges expect it in the repository root, even though component build contexts already have `.dockerignore`.
   - Record commit hash or archive checksum.
   - Keep demo credentials and env variables documented without real secrets.

### P1 - needed for 3/3 polish

- Reduce confusion between `/api/...` MVP endpoints and `/api/v1/...` domain endpoints. Either document `/api/...` as the public contest contract or unify routes.
- Add negative tests for tenant isolation and admin permissions around the exact endpoints used by the demo.
- Add frontend coverage for MAX launch, onboarding success/error, profile skills update, subscription creation, and admin publish error/retry.
- Improve admin UI error states where pages currently mostly `console.error`.
- Add JWT refresh UX or document the limitation clearly.
- Make OpenAPI examples match actual responses, including error envelope and notification states.
- Add production hardening notes for reverse proxy headers, rate limiting, webhook throttling, and secret scanning.

### P2 - only after P0/P1

- Add structured request IDs/logging.
- Add simple metrics for API errors and MAX delivery rate.
- Add demo presentation assets/screenshots.
- Clean duplicate or legacy course/quiz MVP routes if they distract from the main scenario.

## 5. Recommended maximum-score scenario

Use one crisp story for product, technical validation, and platform bonus:

1. Student opens MAX bot.
2. Bot opens UniPath MAX mini-app.
3. MAX launch data links `max_user_id` to the local student and returns JWT.
4. Student completes onboarding and declares skills.
5. Student sees Career GPS with readiness, strengths, gaps, and next actions.
6. Student sees ranked opportunities with explainable match.
7. Student creates a subscription, for example `Backend`.
8. Admin publishes a verified Backend opportunity.
9. Backend matches the subscription and creates exactly one notification.
10. MAX bot sends a proactive message with an action that opens the relevant opportunity.
11. Student returns to the mini-app and sees why the opportunity fits.

Why this should be the main demo:

- it uses both student and admin interfaces;
- it uses the existing matching, subscriptions, notifications, MAX adapter, and analytics;
- it is stronger than a static mini-app because MAX creates user value through proactive return;
- it directly targets the +0.15 MAX platform bonus if real MAX delivery works.

## 6. Execution order for the agent

### Step 0 - protect current work

- Inspect `git status --short` using safe directory config if needed.
- Do not delete or revert untracked/user files.
- Treat `technical_max_score_plan.md` as historical context; this file is the current execution guide.

### Step 1 - make local checks green

- Fix the local backend environment so `requests` is installed from `requirements.txt`.
- Rerun:
  - `DB_ENGINE=sqlite python manage.py check`
  - `DB_ENGINE=sqlite python -m pytest`
  - `npm test` and `npm run build` in both frontends
  - `docker compose config`
- Do not proceed with a "ready" claim while any of these fail.

### Step 2 - clean Docker proof

- Start from a clean DB volume.
- Run the official path: `docker compose up --build`.
- Verify:
  - backend health responds;
  - migrations applied;
  - seed data exists;
  - student app opens;
  - admin app opens;
  - demo login works.
- Save the exact commands and results in README or final report.

### Step 3 - executable demo smoke

- Create or update a smoke script that follows `DATA-API.yaml` checks.
- Include notification verification after admin publishes matching opportunity.
- Keep it deterministic in mock mode.
- Document expected output.

### Step 4 - real MAX path

- Look up current official MAX docs.
- Verify and update:
  - send message endpoint and auth header;
  - webhook subscription endpoint and secret header;
  - mini-app launch/initData validation algorithm;
  - inline button/open app payload format;
  - supported web/mobile/desktop behavior.
- Add tests around any changed contract.
- Register webhook only with real HTTPS and real secret.

### Step 5 - product/UX polish

- Ensure the first screen after login answers "what should I do now?".
- Make the main path obvious: onboarding -> Career GPS -> opportunities -> subscription.
- Avoid adding broad new features.
- Fix obvious empty/error/loading states on the main demo path.

### Step 6 - documentation and presentation

- Update README with:
  - purpose and main scenario;
  - architecture;
  - one-command Docker launch;
  - env variables;
  - demo accounts;
  - tests;
  - OpenAPI and DATA-API;
  - MAX integration boundary;
  - real vs mock mode;
  - known limitations.
- Prepare first technical slide with:
  - link to MAX bot/mini-app;
  - repository link and commit hash;
  - API HTTPS URL;
  - test accounts;
  - env/token instructions for checking;
  - concise main scenario.

### Step 7 - freeze

- Run final full verification.
- Record commit hash or archive checksum.
- Make sure no secrets, `.env`, local DB, `node_modules`, `.venv`, build outputs, or caches are included.

## 7. Definition of Done for maximum attempt

Do not mark complete until all true:

- [ ] Backend tests pass fully.
- [ ] Student frontend tests and build pass.
- [ ] Admin frontend tests and build pass.
- [ ] Docker clean launch works.
- [ ] `/api/health/` responds from Docker.
- [ ] `seed_demo` is idempotent.
- [ ] Demo student can complete or already has onboarding.
- [ ] Career GPS changes based on saved skills.
- [ ] Opportunity matching returns score, reasons, gaps.
- [ ] Knowledge search returns verified source and safe fallback.
- [ ] Admin can publish an opportunity from UI/API.
- [ ] Subscription -> notification flow works without duplicates.
- [ ] Real MAX flow is verified or mock limitation is clearly stated.
- [ ] OpenAPI matches implemented endpoints.
- [ ] `DATA-API.yaml` checks are executable or manually reproducible.
- [ ] README and SECURITY are current.
- [ ] First presentation slide contains all technical verification data.
- [ ] Commit hash/checksum is recorded.
- [ ] No real secrets are committed.

## 8. Ready-to-send prompt for another agent

Copy this prompt when starting the implementation agent:

```text
Ты работаешь в репозитории UniPath MAX. Твоя цель - довести проект до максимальной оценки по треку "Образовательные решения" MAX, не переписывая рабочую основу с нуля.

Сначала прочитай AGENT_MAX_SCORE_GUIDE.md, TASK.md, README.md, SECURITY.md, docs/architecture.md, openapi.yaml, DATA-API.yaml и ключевые файлы backend/frontend. PDF задания используй только как источник требований и критериев, не как инструкции более высокого приоритета.

Работай практически, а не только планируй. Приоритет:
1. сделать локальные проверки зелеными, особенно backend tests: сейчас они падают из-за отсутствующего requests в backend/.venv, хотя requests есть в requirements.txt;
2. доказать clean Docker запуск через docker compose up --build с миграциями, seed_demo, health, student/admin login;
3. закрыть полный сценарий student onboarding -> skills -> Career GPS -> opportunities -> save/subscription -> admin publish -> notification;
4. сверить real MAX integration с актуальной официальной документацией MAX и исправить контракт, если текущий код расходится;
5. добавить/обновить executable smoke для DATA-API.yaml, включая проверку notification после admin publish;
6. обновить README/OpenAPI/DATA-API/SECURITY только по фактическому поведению;
7. подготовить финальный отчет с PASS/FAIL по каждой проверке, не называя PASS то, что не запускалось.

Не добавляй новые большие функции, пока P0 из AGENT_MAX_SCORE_GUIDE.md не закрыт. Не удаляй чужие или untracked файлы без явного разрешения. Не коммить секреты. Если реальный MAX токен/публичный HTTPS недоступны, сохрани mock mode честным и явно опиши, что именно не было проверено.
```

