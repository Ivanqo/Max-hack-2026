# UniPath MAX — TASK.md

## 0. Роль и цель

Ты работаешь как senior full-stack engineer и должен реализовать **рабочий MVP UniPath MAX** в текущей директории проекта.

Главная цель — не сделать mock-up или набор несвязанных экранов, а получить **запускаемый end-to-end продукт** на стеке:

- Backend: Python + Django + Django REST Framework
- Frontend: React + TypeScript
- Database: PostgreSQL
- API: REST/JSON
- Локальный запуск: Docker Compose
- Тестирование backend: pytest / pytest-django либо Django test framework
- Тестирование frontend: Vitest + React Testing Library
- E2E / smoke-проверка: Playwright либо простой автоматизированный smoke-набор
- Документация: README.md + .env.example

Если в репозитории уже есть работающий стек, структура, библиотеки или соглашения, **сначала изучи их и сохраняй совместимость**. Не переписывай рабочую часть проекта без необходимости.

---

# 1. Что такое UniPath MAX

**UniPath MAX** — персональный цифровой навигатор студента: от первого дня в вузе до первой работы.

Студент получает единую точку входа для:

1. поиска проверенной информации университета;
2. понимания карьерной цели и skill gap;
3. получения подходящих стажировок, проектов, хакатонов и мероприятий;
4. подписки на интересующие темы и получения релевантных уведомлений.

Университет получает web-панель для:

- управления проверенной базой знаний;
- публикации возможностей;
- управления аудиториями;
- управления карьерными ролями и навыками;
- просмотра аналитики запросов студентов;
- контроля актуальности информации;
- управления администраторами и ролями.

Ключевой принцип:

> AI не является ядром продукта. Основная ценность должна работать без LLM.

Основу продукта составляют собственные:

- данные;
- business logic;
- matching;
- skill-gap logic;
- subscriptions;
- RBAC;
- analytics;
- verified knowledge;
- fallback-механизмы.

AI/LLM можно предусмотреть как **опциональный адаптер**, но MVP не должен зависеть от внешней генеративной модели.

---

# 2. Приоритет разработки

Главная цель — законченные end-to-end сценарии.

Не пытайся реализовать максимальное количество функций.

Приоритет:

1. работоспособность;
2. четыре основных пользовательских сценария;
3. понятная архитектура;
4. корректная модель данных;
5. RBAC;
6. multi-tenant ready;
7. стабильность;
8. тесты;
9. seed/demo data;
10. документация.

Не делай преждевременно:

- микросервисную архитектуру;
- Kubernetes;
- event sourcing;
- сложный ML;
- собственную LMS;
- социальную сеть;
- сложный workflow/BPMN;
- web crawler;
- AI-психолога;
- мобильное приложение вне MAX.

Для MVP используй **модульный монолит Django**.

---

# 3. Пользователи и роли

Минимальные роли:

## STUDENT

Может:

- пройти onboarding;
- заполнить профиль;
- выбрать карьерную цель;
- указать навыки;
- просматривать Career GPS;
- искать информацию;
- просматривать возможности;
- получать match score;
- подписываться на темы;
- сохранять возможности;
- отправлять report на неактуальный материал.

## EDITOR

Может:

- создавать и редактировать knowledge items;
- создавать opportunities;
- публиковать материалы;
- задавать аудиторию.

## INSTITUTE_ADMIN

Имеет права EDITOR плюс:

- управляет материалами института;
- видит аналитику своего института;
- управляет редакторами института.

## UNIVERSITY_ADMIN

Имеет доступ ко всему tenant/university:

- пользователи;
- контент;
- роли;
- аналитика;
- аудит;
- справочники.

---

# 4. Multi-tenant модель

Архитектура должна быть готова к модели:

> один backend → несколько университетов.

Основная tenant-сущность:

```text
University
```

Все ключевые данные должны принадлежать университету напрямую или косвенно.

Не допускай чтения или изменения данных другого university через API.

Минимально проверить tenant isolation тестами.

---

# 5. Backend modules

Рекомендуемая Django-структура:

```text
backend/
    config/
    apps/
        accounts/
        universities/
        profiles/
        knowledge/
        careers/
        opportunities/
        subscriptions/
        notifications/
        analytics/
        audit/
```

Допустима другая структура, если она логична и уже используется в проекте.

Не дроби код на десятки файлов без необходимости.

---

# 6. Минимальная модель данных

## University

Поля:

- id
- name
- slug
- settings
- created_at
- updated_at

---

## User

Использовать кастомную Django User model с самого начала, если проект создаётся с нуля.

Минимально:

- id
- email / username
- role
- university
- is_active

---

## StudentProfile

- user
- university
- institute
- course
- program
- interests
- career_goal
- onboarding_completed

---

## KnowledgeItem

- university
- title
- content
- source_url
- responsible_unit
- audience
- verified_status
- published
- actual_until или updated_at
- created_by
- created_at
- updated_at

`verified_status` минимум:

```text
draft
verified
outdated
```

Каждый пользовательский ответ по базе знаний должен позволять понять:

- источник;
- статус;
- дату актуальности.

---

## Skill

- university nullable либо global
- name
- category

---

## CareerRole

- university
- name
- description
- active

---

## CareerRoleSkill

- career_role
- skill
- required_level
- weight

---

## StudentSkill

- student
- skill
- level
- evidence optional

---

## Opportunity

Типы:

```text
internship
vacancy
project
hackathon
event
course
```

Поля:

- university
- type
- title
- description
- requirements
- audience
- deadline
- source_url
- verified_status
- published
- created_by
- created_at
- updated_at

---

## OpportunitySkill

- opportunity
- skill
- required_level
- weight

---

## Subscription

- student
- topic
- filters
- active

---

## SavedOpportunity

- student
- opportunity
- created_at

---

## MatchResult

Можно вычислять динамически или хранить.

Минимальный контракт:

- student
- opportunity
- score 0..100
- reasons[]
- gaps[]
- calculated_at

---

## InteractionEvent

Для продуктовой аналитики:

- university
- user optional
- event_type
- entity_type optional
- entity_id optional
- metadata
- created_at

Примеры:

```text
knowledge_search
knowledge_open
knowledge_no_answer
opportunity_open
opportunity_save
career_gps_open
subscription_created
```

---

## AuditLog

- university
- admin
- action
- entity_type
- entity_id
- metadata
- timestamp

Фиксировать минимум:

- создание;
- изменение;
- публикацию;
- снятие с публикации;
- удаление критичного контента.

---

## KnowledgeReport

- university
- student
- knowledge_item
- reason
- status
- created_at

---

# 7. MVP Scenario 1 — Verified Knowledge

Сценарий:

> Студент спрашивает: «Как оформить производственную практику?»

Backend должен:

1. учитывать university;
2. учитывать профиль/аудиторию;
3. искать только опубликованные материалы;
4. отдавать релевантный результат;
5. отдавать source_url;
6. отдавать updated_at / actual_until;
7. отдавать verified_status.

Для MVP достаточно реализовать предсказуемый поиск:

- PostgreSQL full-text search;
- icontains;
- trigram;
- либо комбинацию.

Не создавай внешний AI как обязательную зависимость.

## Fallback

Если релевантный подтвержденный материал не найден:

API должен вернуть корректный ответ вида:

```json
{
  "found": false,
  "message": "Не найден подтвержденный актуальный материал.",
  "escalation": {
    "unit": "...",
    "contact": "..."
  }
}
```

Нельзя генерировать выдуманный ответ.

Обязательно логировать `knowledge_no_answer`.

---

# 8. MVP Scenario 2 — Career GPS

Студент выбирает CareerRole.

Пример:

```text
Backend Developer
```

Для роли есть набор required skills.

У студента есть StudentSkill.

Career GPS должен вернуть:

```json
{
  "career_role": "Backend Developer",
  "readiness_score": 65,
  "strengths": [],
  "gaps": [],
  "next_actions": []
}
```

Пример:

```text
Python — уверенно
SQL — базово
Docker — отсутствует
CI/CD — отсутствует
```

Результат:

- strengths;
- gaps;
- readiness_score;
- 2–3 рекомендуемых следующих действия.

Scoring должен быть детерминированным и покрытым unit tests.

---

# 9. MVP Scenario 3 — Smart Opportunities

Администратор создаёт Opportunity и указывает:

- тип;
- аудиторию;
- skills;
- required levels;
- deadline;
- source;
- verified status.

Matching engine должен вычислять score для студента.

Пример результата:

```json
{
  "score": 86,
  "reasons": [
    "Подходит Python",
    "Подходит PostgreSQL"
  ],
  "gaps": [
    "Не хватает Docker"
  ]
}
```

Не использовать LLM для score.

Score должен быть объяснимым.

Например:

```text
score =
skill_match
+ audience_match
+ interest_match
+ career_goal_match
```

Формула должна быть:

- понятной;
- вынесенной в отдельный service;
- покрытой тестами.

Frontend должен показать:

- процент совпадения;
- почему подходит;
- чего не хватает.

---

# 10. MVP Scenario 4 — Smart Subscriptions

Студент может подписаться минимум на:

- Backend;
- AI;
- стажировки;
- хакатоны;
- практика;
- кафедра/институт.

При появлении релевантной Opportunity должна формироваться Notification.

Для hackathon MVP реальную MAX доставку разрешается реализовать через отдельный adapter.

Пример:

```text
NotificationService
    create_notification()
    send()
```

Adapter:

```text
MAXNotificationAdapter
```

Если MAX credentials/API недоступны, приложение всё равно должно работать.

В таком случае:

- Notification сохраняется в БД;
- статус показывает pending / simulated;
- имеется mock/dev adapter;
- интеграционная граница документирована.

Не скрывай отсутствие внешней интеграции фиктивным успешным API-вызовом.

---

# 11. MAX integration boundary

Проект должен быть архитектурно готов к:

- MAX bot;
- MAX mini app;
- MAX notifications.

Но backend не должен зависеть от недоступного внешнего API.

Создать integration layer, например:

```text
integrations/max/
```

Минимальный интерфейс:

```python
class MaxClient:
    def send_message(...)
    def send_notification(...)
```

Реализации:

```text
MockMaxClient
RealMaxClient
```

`RealMaxClient` может быть stub только в части внешнего HTTP-вызова, если нет подтвержденной документации или credentials.

Но внутренний flow:

```text
event → matching → notification → adapter
```

должен реально работать и тестироваться.

---

# 12. Web Admin

Нужен отдельный React-интерфейс администратора.

Минимальные разделы:

## Dashboard

Показать:

- количество студентов;
- опубликованные knowledge items;
- активные opportunities;
- top search queries;
- unanswered queries;
- самые просматриваемые opportunities.

---

## Knowledge

CRUD:

- создать;
- изменить;
- опубликовать;
- снять с публикации;
- verified status;
- source;
- responsible unit;
- audience.

---

## Opportunities

CRUD:

- создать;
- изменить;
- опубликовать;
- deadline;
- requirements;
- required skills;
- аудитория.

---

## Career roles

CRUD:

- CareerRole;
- required skills;
- levels;
- weights.

---

## Analytics

Минимум:

- популярные запросы;
- вопросы без ответа;
- просмотры opportunities;
- сохранения;
- темы с дефицитом материалов.

---

# 13. Student frontend / Mini App UI

Реализовать student-facing интерфейс на React.

Основная UX-идея:

> главный экран отвечает на вопрос «что мне сделать сейчас?»

Не делай меню из 20 пунктов.

Минимальные страницы:

## Onboarding

Поля:

- university;
- institute;
- course;
- program;
- interests;
- career goal.

Для demo university может быть предвыбран.

---

## Home

Карточки:

- Career GPS;
- подходящие возможности;
- поиск по вузу;
- подписки.

---

## Knowledge Search

- поле запроса;
- результат;
- source;
- дата;
- verified badge;
- fallback.

---

## Career GPS

- выбранная цель;
- readiness;
- strengths;
- gaps;
- next actions.

---

## Opportunities

- карточки;
- match percentage;
- reasons;
- gaps;
- deadline;
- save.

---

## Profile / Skills

- профиль;
- career goal;
- skills;
- subscriptions.

---

# 14. API

API должен иметь понятную структуру.

Пример:

```text
/api/v1/auth/
/api/v1/profile/
/api/v1/knowledge/
/api/v1/careers/
/api/v1/opportunities/
/api/v1/subscriptions/
/api/v1/notifications/
/api/v1/analytics/
/api/v1/admin/
```

Использовать:

- serializers;
- permissions;
- service layer для сложной business logic;
- pagination;
- filtering;
- validation;
- нормальные HTTP statuses.

Не помещать сложную business logic в serializers/views.

---

# 15. Authentication

Для MVP:

- Django auth;
- JWT через SimpleJWT допустим и предпочтителен для SPA.

Не хранить auth token небезопасным способом без необходимости.

Добавить demo users через seed.

---

# 16. Seed Data

Обязательно создать команду:

```bash
python manage.py seed_demo
```

Она должна быть idempotent.

Создать минимум:

## Universities

2 университета/tenant для демонстрации tenant isolation.

## Demo accounts

Например:

```text
student@demo.local
editor@demo.local
admin@demo.local
```

Пароли документировать только как demo credentials в README.

## Careers

3–5 ролей:

- Backend Developer
- Data Analyst
- ML Engineer
- Product Analyst
- DevOps Engineer

## Skills

Минимум:

- Python
- SQL
- Django
- REST
- Docker
- Git
- CI/CD
- PostgreSQL
- Linux
- Data Analysis

## Opportunities

10–20 realistic demo opportunities.

## Knowledge

20–30 realistic university materials.

Особенно материалы про:

- практику;
- стипендию;
- справки;
- воинский учёт;
- академический отпуск;
- карьерный центр;
- общежитие;
- студенческие проекты.

---

# 17. Analytics

Не строить сложный BI.

Использовать InteractionEvent.

Минимальные backend queries:

```text
GET /api/v1/analytics/top-queries/
GET /api/v1/analytics/unanswered/
GET /api/v1/analytics/opportunities/
GET /api/v1/analytics/overview/
```

Frontend должен отображать понятные показатели.

---

# 18. Security

Обязательно:

- Django security defaults;
- CORS configurable;
- CSRF учитывать в зависимости от auth;
- password validation;
- API permissions;
- tenant isolation;
- input validation;
- secrets только через env;
- `.env` в `.gitignore`;
- audit действий администраторов;
- минимизация пользовательских данных.

Не логировать:

- passwords;
- access tokens;
- refresh tokens;
- чувствительные payload без необходимости.

---

# 19. Error handling

API должен отдавать единый понятный JSON error contract.

Например:

```json
{
  "error": {
    "code": "KNOWLEDGE_NOT_FOUND",
    "message": "Не найден подтвержденный материал.",
    "details": {}
  }
}
```

Frontend:

- loading state;
- empty state;
- error state;
- retry там, где уместно.

Не должно быть:

- необработанных 500;
- пустых экранов;
- бесконечных loaders.

---

# 20. Docker

Проект должен запускаться командой:

```bash
docker compose up --build
```

Минимальные services:

```text
backend
frontend
db
```

Допустим nginx, если он реально нужен.

После запуска:

- frontend доступен из браузера;
- backend health endpoint отвечает;
- DB migrations применяются корректно.

Добавить health endpoint:

```text
GET /api/health/
```

Ответ:

```json
{
  "status": "ok"
}
```

---

# 21. Environment

Создать:

```text
.env.example
```

Минимум:

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=
CORS_ALLOWED_ORIGINS=
MAX_API_URL=
MAX_BOT_TOKEN=
MAX_INTEGRATION_MODE=mock
```

Не коммитить реальные secrets.

---

# 22. Tests

Работа не считается выполненной без тестов.

## Backend

Покрыть минимум:

- authentication;
- permissions;
- tenant isolation;
- knowledge search;
- knowledge fallback;
- career gap calculation;
- opportunity matching;
- subscriptions;
- admin CRUD;
- analytics;
- seed command.

Особое внимание business logic:

```text
CareerGPSService
OpportunityMatchingService
KnowledgeSearchService
```

---

## Frontend

Минимум:

- ключевые компоненты;
- Career GPS rendering;
- knowledge result/fallback;
- opportunity match card;
- auth protected routes.

---

## E2E / Smoke

Проверить минимум один end-to-end demo journey:

1. login student;
2. открыть Career GPS;
3. увидеть gaps;
4. открыть подходящую opportunity;
5. увидеть match/reasons;
6. выполнить knowledge search;
7. получить verified source.

И admin journey:

1. login admin;
2. создать opportunity;
3. publish;
4. убедиться, что студент может её получить.

---

# 23. Definition of Done

Проект считается готовым только если выполняются все пункты:

- [ ] Backend запускается.
- [ ] Frontend запускается.
- [ ] PostgreSQL подключается.
- [ ] migrations применяются на чистой БД.
- [ ] seed_demo успешно выполняется.
- [ ] demo login работает.
- [ ] onboarding работает.
- [ ] Knowledge Search работает.
- [ ] Verified source показывается.
- [ ] Knowledge fallback работает.
- [ ] Career GPS работает.
- [ ] Opportunity Matching работает.
- [ ] score объясним.
- [ ] Opportunity CRUD работает.
- [ ] Knowledge CRUD работает.
- [ ] subscriptions работают.
- [ ] notifications создаются.
- [ ] admin analytics работает.
- [ ] tenant isolation проверен.
- [ ] backend tests проходят.
- [ ] frontend tests проходят.
- [ ] E2E/smoke test проходит.
- [ ] `/api/health/` отвечает.
- [ ] проект поднимается через Docker Compose.
- [ ] README содержит точную инструкцию запуска.
- [ ] `.env.example` существует.
- [ ] demo credentials указаны.
- [ ] отсутствуют критические TODO в основных сценариях.
- [ ] нет mock UI вместо основной backend logic.

---

# 24. Проверка работоспособности

Перед завершением задачи ОБЯЗАТЕЛЬНО самостоятельно проверить проект.

Если окружение позволяет Docker:

```bash
docker compose down -v
docker compose up --build -d
```

Затем:

```bash
docker compose ps
```

Проверить health API.

Запустить backend tests.

Запустить frontend tests.

Запустить E2E/smoke tests.

Просмотреть logs на наличие runtime errors.

Если Docker недоступен в текущем окружении:

1. выполнить максимально возможную локальную проверку;
2. запустить линтеры/tests/build;
3. явно указать, что именно невозможно было проверить;
4. НЕ утверждать, что Docker-проверка выполнена, если она не выполнялась.

---

# 25. README

README должен содержать:

1. описание проекта;
2. архитектуру;
3. структуру директорий;
4. требования;
5. quick start;
6. Docker запуск;
7. env variables;
8. migrations;
9. seed data;
10. demo users;
11. запуск tests;
12. API overview;
13. описание matching;
14. описание Career GPS;
15. MAX integration boundary;
16. известные ограничения MVP.

---

# 26. Architecture documentation

Добавить:

```text
docs/architecture.md
```

Описать:

```text
React Student UI ─┐
                  ├── Django REST API ─── PostgreSQL
React Admin UI ───┘        │
                           ├── Matching Engine
                           ├── Career GPS
                           ├── Knowledge Search
                           ├── Analytics
                           └── MAX Integration Adapter
```

Объяснить:

- почему modular monolith;
- tenant isolation;
- service layer;
- integration boundaries;
- возможность дальнейшего масштабирования.

---

# 27. Coding quality

Код должен быть пригоден для чтения другим разработчиком.

Правила:

- понятные имена;
- небольшие функции с одной ответственностью;
- избегать дублирования;
- избегать god objects;
- type hints в Python там, где полезно;
- TypeScript strict mode;
- не использовать `any` без причины;
- бизнес-правила отделять от HTTP;
- комментарии писать только там, где логика неочевидна;
- не создавать бессмысленные wrapper-ы;
- не дробить одну простую функцию на пять файлов.

---

# 28. Порядок работы агента

Работай последовательно.

## Step 1 — Repository inspection

Сначала изучи:

- существующие файлы;
- git status;
- README;
- package.json;
- requirements/pyproject;
- Docker;
- backend;
- frontend;
- существующие tests.

Не удаляй существующую реализацию без необходимости.

---

## Step 2 — Plan

Составь внутренний реалистичный план.

Определи:

- что уже реализовано;
- что отсутствует;
- какие модули изменить;
- минимальный путь до работающего MVP.

Не останавливайся после плана.

---

## Step 3 — Foundation

Если проект пустой:

1. создать Django backend;
2. создать React + TypeScript frontend;
3. PostgreSQL;
4. Docker Compose;
5. authentication;
6. base routing.

---

## Step 4 — Core business model

Реализовать:

- University;
- User/RBAC;
- StudentProfile;
- skills/careers;
- Knowledge;
- Opportunities;
- subscriptions;
- analytics/audit.

---

## Step 5 — Business services

Реализовать и протестировать:

- KnowledgeSearchService;
- CareerGPSService;
- OpportunityMatchingService;
- NotificationService.

---

## Step 6 — API

Реализовать API для основных сценариев.

---

## Step 7 — Frontend

Реализовать сначала рабочие flows, затем UI polish.

---

## Step 8 — Seed

Создать реалистичные demo data.

---

## Step 9 — Tests

Добавить tests одновременно с business logic, а не в самом конце.

---

## Step 10 — Integration verification

Поднять проект с чистой БД и пройти demo journey.

---

# 29. Приоритет при нехватке времени

Если весь backlog невозможно закончить в рамках текущей работы, приоритет строго такой:

## P0

1. Django + React + PostgreSQL запускаются.
2. Auth + RBAC.
3. Student Profile.
4. Knowledge + verified/fallback.
5. Career GPS.
6. Opportunities.
7. Matching.
8. Admin CRUD.
9. Seed.
10. Tests.
11. Docker.
12. README.

## P1

13. Subscriptions.
14. Notifications.
15. Analytics.
16. Audit.

## P2

17. MAX real adapter.
18. advanced search.
19. advanced charts.
20. optional AI.

Не оставляй P0 недоделанным ради P2.

---

# 30. Что запрещено считать завершением

Нельзя заканчивать работу сообщением вида:

- «архитектура подготовлена»;
- «создан skeleton»;
- «можно дальше реализовать»;
- «frontend пока mock»;
- «tests можно добавить позже»;
- «осталось подключить backend»;
- «реализация представлена частично».

Нужно довести максимально возможную часть проекта до **работающего состояния**.

---

# 31. Финальный отчёт агента

После реализации выдай краткий отчёт:

```text
IMPLEMENTATION SUMMARY

Implemented:
- ...

Architecture:
- ...

Tests:
- backend: ...
- frontend: ...
- e2e: ...

Runtime verification:
- docker compose: PASS/FAIL/NOT AVAILABLE
- backend health: PASS/FAIL
- frontend build: PASS/FAIL
- migrations: PASS/FAIL
- seed: PASS/FAIL

Demo:
- frontend URL:
- backend URL:
- admin credentials:
- student credentials:

Known limitations:
- ...

Main changed files:
- ...
```

Не пиши PASS, если проверка фактически не выполнялась.

---

# 32. Итоговая продуктовая проверка

Перед завершением задай себе вопросы:

1. Может ли новый студент пройти onboarding?
2. Может ли он выбрать карьерную цель?
3. Видит ли он skill gap?
4. Может ли он получить подходящую opportunity?
5. Объясняется ли match?
6. Может ли он найти университетскую информацию?
7. Видит ли он источник и актуальность?
8. Есть ли безопасный fallback?
9. Может ли admin опубликовать материал без ручной работы с БД?
10. Может ли admin опубликовать opportunity?
11. Попадает ли новая opportunity в student flow?
12. Видит ли admin реальные interaction events?
13. Не может ли пользователь одного tenant читать данные другого?
14. Можно ли поднять проект по README на чистом окружении?

Если хотя бы один критический P0-сценарий сломан — исправь его до завершения задачи.
