# Pause Notes

Дата обновления: 2026-09-09

## Текущее состояние

Работа по MVP из `TASK.md` доведена до финальной проверки, кроме полного Docker runtime: Docker Desktop/daemon на машине не запущен или недоступен (`dockerDesktopLinuxEngine` pipe не найден).

## Что реализовано

- Backend: добавлены university/tenant context, MVP API routes, onboarding, student opportunities, save opportunity, subscriptions, Career GPS, verified knowledge search, admin CRUD/audit, analytics extensions, unified DRF errors.
- Services: `KnowledgeSearchService`, `CareerGPSService`, `OpportunityMatchingService`, notification service with mock/simulated MAX delivery.
- Seed: `python manage.py seed_demo` идемпотентно создаёт 2 tenants, demo users, career roles, skills, opportunities, knowledge items, subscriptions and notifications.
- Frontend student: маршруты переключены на MVP pages; API calls синхронизированы с backend; добавлены Vitest/RTL tests.
- Frontend admin: добавлены Vitest/RTL tests; вход разрешает manager roles (`admin`, `editor`, `institute_admin`, `university_admin`).
- Docs/env: добавлены root `README.md`, `docs/architecture.md`, обновлены `.env.example`, `backend/.env.example`, `DOCKER.md`, `docker-compose.yml`.
- Migrations: добавлены недостающие migrations для новых/изменённых моделей и choices.

## Проверки

- Backend tests: PASS, `36 passed`.
- Backend migrations: PASS, `migrate --noinput`, затем `makemigrations --check --dry-run` -> `No changes detected`.
- Seed: PASS, `seed_demo` повторно выполняется.
- Student frontend tests: PASS, `5 passed`.
- Admin frontend tests: PASS, `2 passed`.
- Student frontend build: PASS.
- Admin frontend build: PASS.
- Docker compose config: PASS.
- Docker compose up/build: NOT AVAILABLE, Docker daemon недоступен.
- Local backend health/API smoke: PASS, `/api/health/` и авторизованный `/api/knowledge/search?q=практика`.

## Если продолжать дальше

1. Запустить Docker Desktop.
2. Выполнить:

```powershell
docker compose up --build -d
docker compose exec backend python manage.py seed_demo
docker compose ps
```

3. Проверить http://localhost:3000, http://localhost:3001 и http://localhost:8000/api/health/.
