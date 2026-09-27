# UniPath MAX — техническая документация

Инструкция по локальному запуску, структуре репозитория, тестовым данным и API. Секреты и рабочие учетные данные в README не публикуются.

## Требования

- Docker Engine или Docker Desktop с Docker Compose — для полного локального запуска;
- Node.js 20 и npm — только если запускать Vite-интерфейсы отдельно от Docker;
- Python 3.11 — если запускать Django-команды вне контейнера.

## Быстрый запуск

Из корня репозитория создайте локальный `.env` и запустите стек:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

В Linux/macOS используйте `cp .env.example .env`. При необходимости отредактируйте `.env` перед запуском. Значения из примера предназначены для локального стенда, не для публичного развертывания.

Compose запускает PostgreSQL, Django API и два frontend-сервиса. Backend ожидает готовности БД, применяет миграции и при `AUTO_SEED_DEMO=true` загружает демонстрационные данные.

| Сервис | Локальный адрес | Настройка порта |
| --- | --- | --- |
| Student frontend | `http://localhost:3000` | `STUDENT_PORT` |
| Admin frontend | `http://localhost:3001` | `ADMIN_PORT` |
| Django API health | `http://localhost:8000/api/health/` | `BACKEND_PORT` |
| PostgreSQL | `localhost:5432` | порт в `docker-compose.yml` |

Остановить стек, сохранив данные в volume:

```powershell
docker compose down
```

Повторный `docker compose up --build -d` подключится к той же базе. `docker compose down -v` удаляет volume PostgreSQL и все данные локального стенда.

## Переменные окружения

Полный шаблон — в `.env.example`; Docker Compose читает `.env` из корня.

| Группа | Переменные |
| --- | --- |
| PostgreSQL | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DATABASE_URL` |
| Django | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` |
| Порты | `BACKEND_PORT`, `STUDENT_PORT`, `ADMIN_PORT` |
| Frontend/build | `VITE_API_URL`, `NODE_ENV`, `BUILD_TARGET`, `VOLUME_MODE` |
| Seed | `AUTO_SEED_DEMO` |
| MAX | `MAX_API_URL`, `MAX_INTEGRATION_MODE`, `MAX_BOT_TOKEN`, `MAX_WEBHOOK_SECRET`, `MAX_WEBHOOK_URL`, `MAX_OPEN_APP_TARGET`, `MAX_WEBAPP_BASE_URL`, `MAX_INITDATA_MAX_AGE_SECONDS` |

`VOLUME_MODE` также присутствует в `.env.example`, но текущий корневой `docker-compose.yml` эту переменную не использует.

Не коммитьте `.env`, токены MAX, секрет webhook, реальные пароли или ключи. Храните production-секреты в системе управления секретами; дополнительные указания находятся в [SECURITY.md](SECURITY.md).

## Seed и демонстрационные данные

Команда `python manage.py seed_demo` доступна из каталога `backend/`. В Docker она вызывается при старте, если `AUTO_SEED_DEMO=true` (значение в `.env.example`). Команда идемпотентно создает или обновляет тестовые записи для двух университетских контекстов: пользователей, профили, навыки, карьерные роли, возможности, материалы базы знаний и подписки. Это синтетические данные, не выгрузка из систем МГСУ или МАИ.

Seed выводит тестовые логины и пароли в журнал backend. Используйте их только в локальной демонстрационной базе; не копируйте журналы с учетными данными в публичные материалы. Не используйте демо-пароли в публичном развертывании. Чтобы просмотреть локальный вывод:

```powershell
docker compose logs backend
```

Для запуска seed вручную в работающем контейнере:

```powershell
docker compose exec backend python manage.py seed_demo
```

## Структура репозитория

```text
backend/          Django REST Framework API и доменные приложения
frontend-student/ React + TypeScript + Vite интерфейс студента
frontend-admin/   React + TypeScript + Vite интерфейс администратора
deploy/           конфигурация reverse proxy и сертификаты для API MAX
docs/             архитектурные заметки
scripts/          сборка вспомогательных материалов
output/           подготовленные материалы и отчеты проекта
docker-compose.yml локальная конфигурация PostgreSQL, API и frontend
openapi.yaml      контракт API
DATA-API.yaml     декларация проверок API
```

Backend организован как модульный Django-проект. Основные приложения в `backend/apps/`: `accounts`, `profiles`, `careers`, `opportunities`, `subscriptions`, `notifications`, `analytics`, `knowledge`, `universities`. Сборка выполняется Docker multi-stage файлами `backend/Dockerfile`, `frontend-student/Dockerfile` и `frontend-admin/Dockerfile`.

Зависимости backend перечислены в `backend/requirements.txt`. Фронтенды используют Node.js 20 и зафиксированные `package-lock.json`; контейнеры устанавливают npm-зависимости через `npm ci`.

## Разработка frontend вне Docker

Сначала запустите БД и backend в контейнерах:

```powershell
docker compose up -d db backend
```

В отдельных терминалах:

```powershell
cd frontend-student
npm ci
npm run dev
```

```powershell
cd frontend-admin
npm ci
npm run dev
```

Vite использует порты `3000` и `3001`; оба `vite.config.ts` проксируют `/api` в `http://localhost:8000`. Сборка интерфейса выполняется командой `npm run build` в соответствующем frontend-каталоге.

## API и схемы

Основные локальные маршруты:

- `GET /api/health/` — health check;
- `POST /api/auth/register/`, `POST /api/auth/login/` — регистрация и вход;
- `POST /api/max/launch/`, `POST /api/max/webhook/` — запуск Mini App и webhook MAX;
- `POST /api/onboarding`, `GET /api/student/profile`, `GET /api/student/career-gps`;
- `GET /api/student/opportunities`, `GET /api/student/opportunities/{id}`, `POST /api/student/opportunities/{id}/save`;
- `GET|POST /api/student/subscriptions`;
- `GET /api/v1/notifications/` — список уведомлений авторизованного пользователя;
- `GET /api/knowledge/search?q=...`;
- `GET|POST /api/admin/opportunities`, `GET /api/admin/analytics`.

Полная OpenAPI-спецификация находится в [`openapi.yaml`](openapi.yaml). Проверки конкурса описаны в [`DATA-API.yaml`](DATA-API.yaml); в нем указан публичный base URL и относительные пути. Наличие URL в конфигурации не гарантирует, что удаленный сервис доступен в данный момент.

Ручной технический сценарий приведен в [`DEMO_TEST_SCENARIO.md`](DEMO_TEST_SCENARIO.md). Скрипт `backend/scripts/smoke_data_api.py` обращается к API, создает тестовую подписку и возможность и затем удаляет их; запускайте его только на отдельной локальной или тестовой базе:

```powershell
python backend/scripts/smoke_data_api.py --base-url http://localhost:8000
```

## MAX: режимы и настройка

По умолчанию `MAX_INTEGRATION_MODE=mock`: внешний запрос в MAX не выполняется, а созданная запись имеет статус смоделированной доставки. Для режима `real` нужны действующий `MAX_BOT_TOKEN`, публичные HTTPS адреса приложения и backend, секрет webhook и настроенная Mini App в MAX. Webhook регистрируется командой:

```powershell
docker compose exec backend python manage.py register_max_webhook
```

Ручные прогоны MAX подтвердили только часть сценария: сообщение появилось в тестовом диалоге, переход к карточке сработал после закрытия Mini App, но первый переход без закрытия оставил прежний экран. Проверка переключения связки МГСУ/МАИ и числа доставленных получателей не завершена. Не считайте real-интеграцию полностью проверенной по локальному mock-режиму.

## Технические ограничения

- Отдельного поля оплаты в модели возможности нет.
- Уведомления доступны через backend API; отдельного центра уведомлений в student frontend нет.
- Реальная доставка зависит от конфигурации MAX и привязки MAX ID к профилю.
- Поиск базы знаний выполняется по подготовленным записям; seed-данные синтетические.
- Frontend refresh-flow для JWT ограничен; подробности ведутся в `SECURITY.md`.

Дополнительные инструкции: [DOCKER.md](DOCKER.md), [docs/architecture.md](docs/architecture.md), [SECURITY.md](SECURITY.md).
