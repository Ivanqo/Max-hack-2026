# Технический план доведения MVP до максимальной оценки — трек «Образовательные решения» / MAX

## 1. Цель документа

Документ фиксирует пересечение:

1. **того, что уже реализовано** в переданных архивах `backend.zip`, `frontend-student.zip`, `frontend-admin.zip`, `apps.zip` и в `architecture.md`;
2. **официальных требований кейса** из файла `Образовательные решения.pdf`;
3. **технического backlog**, который необходимо закрыть, чтобы претендовать на максимальную оценку по всем техническим критериям онлайн-этапа и на дополнительный платформенный бонус `+0,15` за расширенное использование MAX.

Основной принцип: не наращивать количество функций ради количества. Сначала необходимо сделать **один полностью работающий, воспроизводимый и проверяемый end-to-end сценарий внутри MAX**, затем закрыть надежность, безопасность, документацию и платформенный бонус.

---

## 2. Что требует кейс

Техническая оценка составляет **60% итогового балла онлайн-этапа** и включает:

| Критерий | Вес внутри технической оценки |
|---|---:|
| Работоспособность и полнота основных функций | 30% |
| Корректность интеграции и обмена данными | 20% |
| Стабильность работы и обработка ошибок | 10% |
| Техническая реализация и архитектура | 20% |
| Безопасность, зависимости и работа с данными | 10% |
| Техническая документация и комплектность материалов | 10% |

Дополнительно может быть начислен **платформенный бонус `+0,15`**, но только целиком. Для него недостаточно самого факта наличия собственного API или большого числа функций. Нужна дополнительная возможность MAX сверх минимального требования, которая дает пользователю ценность, встроена в основной продукт, полностью работает и описана в материалах.

### Обязательные технические условия сдачи

По кейсу должны быть подготовлены:

- работающий чат-бот / мини-приложение в MAX;
- зафиксированная версия исходного кода: commit hash либо архив с контрольной суммой;
- полноценный `README.md`;
- зафиксированные зависимости;
- Dockerfile для нужных компонентов;
- `compose.yaml` / `docker-compose.yml`, запускающий локальные компоненты одной командой;
- `.dockerignore`;
- `.env.example` без рабочих секретов;
- воспроизводимая сборка Docker не более 5 минут без учета первичной загрузки базовых образов;
- при наличии собственного API: публичный HTTPS API, OpenAPI 3.0/3.1, тестовые учетные записи, тестовые данные и `DATA-API.yaml`.

Источник требований: `Образовательные решения.pdf`, стр. 9–10, 13, 15.

---

# 3. Текущее состояние проекта

## 3.1. Архитектурная база — уже сильная

В проекте уже заложена разумная структура MVP:

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

Используется **модульный монолит** на Django: это хороший выбор для хакатонного MVP, поскольку дает один deployable unit, но при этом бизнес-домены разделены на Django apps.

Уже присутствуют отдельные сервисы:

- `KnowledgeSearchService`;
- `CareerGPSService`;
- `OpportunityMatchingService`;
- notification/MAX integration layer;
- аналитика;
- tenant-aware модели и фильтрация по университету.

Это соответствует критерию «логичная архитектура, понятные роли компонентов, отделенная бизнес-логика» и является хорошей основой для высокой оценки.

## 3.2. Уже реализованные продуктовые механики

### Student UI

Активные маршруты:

- авторизация / регистрация;
- onboarding;
- главная;
- база знаний;
- Career GPS;
- возможности / opportunities;
- профиль.

### Admin UI

Реализованы:

- dashboard;
- управление knowledge base;
- управление opportunities;
- управление career roles;
- analytics.

### Backend

Реализованы:

- JWT-аутентификация;
- onboarding и профиль студента;
- Career GPS;
- explainable opportunity matching;
- сохранение opportunities;
- подписки;
- knowledge search;
- административный CRUD;
- аналитика;
- notification service;
- mock / real MAX client abstraction;
- health endpoint;
- тесты по основным backend-доменам.

## 3.3. Сильные технические стороны текущей реализации

1. **Explainable matching**, а не непрозрачный «AI score»: сервис возвращает причины совпадения, gaps и component scores.
2. **Career GPS** формирует readiness, strengths, gaps и next actions.
3. **Knowledge Search** работает только с подтвержденными/актуальными материалами и имеет safe fallback при отсутствии надежного ответа.
4. **MAX изолирован адаптером**, есть `MockMaxClient` и `RealMaxClient`; состояние симуляции не выдается за реальную доставку.
5. Есть идея **tenant isolation** по университету.
6. В production Dockerfile backend используется non-root пользователь и healthcheck.
7. В проекте уже есть `.env.example`, `.dockerignore`, фиксированный `requirements.txt`, `package-lock.json`.
8. Есть backend unit/integration tests и frontend component tests для части ключевых экранов.

---

# 4. Главный вывод аудита

Проект уже выглядит как хорошая **web-заготовка образовательной платформы**, но в текущем виде его нельзя считать готовым конкурсным решением MAX.

Главные blockers максимальной технической оценки:

1. **нет подтвержденного рабочего end-to-end сценария в MAX**;
2. `RealMaxClient` сейчас выглядит как абстрактная заготовка и использует собственные пути вида `/notifications/send`, а не доказанную в проекте интеграцию с актуальным контрактом MAX;
3. в frontend не найдено использование MAX Bridge / MAX UI и нет явной обработки контекста запуска mini-app;
4. отсутствует top-level `compose.yaml` / `docker-compose.yml`;
5. отсутствуют `openapi.yaml/json` и `DATA-API.yaml`, хотя собственный API используется;
6. текущий README не соответствует обязательной структуре кейса;
7. есть критичная проблема авторизации: публичная регистрация позволяет передавать роль пользователя;
8. основной пользовательский сценарий не полностью замкнут на реальные данные: профиль, skills и Career GPS требуют дополнительной связки;
9. недостаточна обработка ошибок на frontend, особенно в admin UI;
10. есть дублирующиеся/legacy-реализации и два API-слоя (`/api/...` и `/api/v1/...`), что ухудшает ясность архитектуры и контракта.

---

# 5. Рекомендуемый основной пользовательский сценарий

Нужно выбрать **один сценарий**, который полностью демонстрируется от начала до результата.

Рекомендуемый сценарий на базе уже написанного кода:

```text
Студент открывает бот в MAX
        ↓
переходит в mini-app
        ↓
проходит onboarding
(университет / программа / интересы / навыки / карьерная цель)
        ↓
получает Career GPS
(readiness + gaps + next actions)
        ↓
получает объяснимую подборку релевантных opportunities
        ↓
сохраняет opportunity и/или создает подписку
        ↓
администратор публикует новую подтвержденную opportunity
        ↓
backend определяет соответствие подписке
        ↓
бот MAX присылает персональное уведомление
        ↓
пользователь открывает из сообщения релевантную opportunity
```

Почему именно этот сценарий:

- большая часть backend уже существует;
- он использует и Student UI, и Admin UI, и matching, и subscriptions, и MAX;
- его легко проверить технически;
- он демонстрирует ценность MAX не как «обертки над сайтом», а как канала взаимодействия и возврата пользователя;
- этот же сценарий можно использовать для получения платформенного бонуса.

---

# 6. Gap analysis по техническим критериям

## 6.1. Работоспособность и полнота основных функций — 30%

### Уже реализовано

- Student UI с ключевыми экранами.
- Admin UI.
- Авторизация.
- Onboarding.
- Career GPS backend + экран.
- Matching opportunities + объяснения.
- Save opportunity.
- Subscription model/service.
- Knowledge Search.
- Admin CRUD.
- Notification layer.
- Тесты ряда доменных сервисов.

### Что мешает максимальной оценке

#### A. Основной сценарий пока не является настоящим MAX-сценарием

MAX adapter в backend есть, но полноценного доступного для жюри сценария внутри MAX в переданных исходниках не видно.

**Нужно:**

- зарегистрировать конкурсного бота;
- реализовать реальные handlers/webhook/polling по актуальному MAX Bot API;
- подключить HTTPS mini-app к боту;
- реализовать идентификацию/связывание MAX-пользователя с профилем приложения;
- проверить desktop/web/mobile варианты, требуемые кейсом;
- подготовить стабильную публичную ссылку на mini-app/API.

#### B. Профиль и навыки не замыкают Career GPS

Активный `ProfilePage.tsx` показывает только имя/e-mail/роль. В проекте присутствует более богатый `Profile.tsx`, но он не подключен к роутингу и использует mock-функции с `setTimeout`.

Backend уже имеет `/api/v1/profiles/.../update-skills/`, поэтому большая часть server-side основы существует.

**Нужно:**

- либо добавить выбор skills в onboarding;
- либо подключить реальное редактирование навыков на активной странице профиля;
- использовать существующий backend API вместо mock;
- после изменения skills инвалидировать/пересчитывать Career GPS и matching.

#### C. Onboarding содержит hardcoded `course = 3`

В `config/mvp_views.py` профиль создается с `course: 3` независимо от пользовательского выбора.

**Нужно:** сохранить реальный курс пользователя либо явно убрать поле из MVP, если оно не влияет на продукт.

#### D. Демо-данные смешаны с рабочей логикой

В `mvp_views.py` есть `DEMO_INSTITUTES`, `DEMO_PROGRAMS`, `DEMO_INTERESTS`, `DEMO_COURSES`, `DEMO_QUIZZES`.

Кейс разрешает модельные данные, но требует **явно это обозначить**.

**Нужно:**

- вынести их в `fixtures/` / seed data;
- маркировать как synthetic/demo;
- описать происхождение в README;
- не выдавать демо-интеграцию за реальную.

### Definition of Done

- fresh user способен пройти сценарий без ручной работы в БД;
- сценарий работает повторно;
- данные пользователя реально влияют на Career GPS и matching;
- все кнопки основного пути выполняют реальное действие;
- MAX является реальной точкой входа и частью результата.

---

## 6.2. Корректность интеграции и обмена данными — 20%

### Уже реализовано

- frontend → Django API;
- backend → PostgreSQL;
- сервисные слои matching / career / knowledge;
- MAX adapter;
- tenant context;
- явные статусы notification (`pending`, `simulated`, `sent`, `failed`).

### Что требуется

#### A. Заменить placeholder MAX API на реальный контракт

`RealMaxClient` сейчас отправляет запросы на:

```text
POST {MAX_API_URL}/notifications/send
GET  {MAX_API_URL}/notifications/{message_id}/status
GET  {MAX_API_URL}/health
```

Из переданных материалов нельзя подтвердить, что эти endpoints соответствуют актуальному официальному API MAX.

**Нужно перед сдачей:**

- свериться с актуальной документацией MAX;
- реализовать реальные методы Bot API;
- добавить webhook validation / безопасную обработку update events;
- сопоставлять MAX user/chat ID с локальным пользователем;
- сохранять external message ID;
- сделать retry/idempotency для отправки;
- логировать request ID / provider response без утечки токенов.

#### B. Убрать неоднозначность API

Сейчас параллельно существуют:

- `/api/...` — MVP facade;
- `/api/v1/...` — ViewSet API доменных приложений.

Это увеличивает вероятность расхождения контрактов.

**Рекомендуется:**

- выбрать один публичный конкурсный API, например `/api/v1/...`;
- сохранить compatibility aliases только если они реально нужны frontend;
- явно пометить deprecated routes;
- не описывать в OpenAPI неиспользуемые endpoints.

#### C. Исправить Admin Opportunities list

Admin UI получает список через `/opportunities`, а CRUD выполняет через `/admin/opportunities`.

Это создает два разных смысловых контракта и потенциально скрывает draft/unverified объекты.

**Нужно:** использовать `/admin/opportunities` и для списка.

#### D. Контракт данных

Добавить:

- единые serializers;
- единый формат ошибок;
- schema validation;
- контрактные тесты;
- OpenAPI validation в CI.

### Definition of Done

- реальные MAX сообщения проходят end-to-end;
- OpenAPI совпадает с работающим API;
- frontend не зависит от скрытых/неописанных форматов;
- статусы, поля и HTTP codes предсказуемы;
- тестами покрыты успешные и ошибочные интеграционные сценарии.

---

## 6.3. Стабильность и обработка ошибок — 10%

### Уже реализовано

- backend healthcheck;
- часть frontend экранов имеет loading/error state;
- notification service переводит неуспешную доставку в `failed`;
- в service есть `retry_failed_notifications()`;
- knowledge search возвращает safe fallback;
- API перехватывает часть ошибок.

### Основные gaps

#### A. Retry не подключен как эксплуатационный механизм

Метод retry присутствует, но не найден scheduler / management command / queue, который выполняет его автоматически.

**Для MVP достаточно:** management command + периодический cron/job либо admin endpoint с RBAC и идемпотентностью.

#### B. Frontend часто только пишет ошибку в `console.error`

Особенно Admin UI.

**Нужно:**

- user-visible error state;
- `Retry`;
- optimistic action rollback;
- disable buttons во время submit;
- понятное сообщение при conflict/validation error;
- graceful empty states.

#### C. Нет полноценного JWT refresh flow во frontend

При `401` токен очищается и пользователь разлогинивается, хотя backend поддерживает refresh token.

**Нужно:**

- refresh interceptor;
- один повтор исходного запроса;
- защита от refresh-loop;
- после окончательной ошибки — controlled logout.

#### D. Exception details могут попасть пользователю

В нескольких местах используются ответы с `str(e)`.

**Нужно:** внутреннюю ошибку логировать, наружу отдавать стабильный безопасный `error_code` + пользовательское сообщение.

#### E. Не хватает негативных тестов

Добавить тесты:

- invalid payload;
- unauthorized/forbidden;
- wrong tenant;
- duplicate request;
- MAX timeout / 4xx / 5xx;
- repeated notification delivery;
- database constraint error;
- empty matching result;
- expired token;
- recovery после временной ошибки.

### Definition of Done

- 20–30 последовательных прохождений demo-flow без ручной очистки состояния;
- повторные POST не создают критичные дубликаты;
- после временной ошибки сценарий можно продолжить;
- пользователь никогда не остается на «мертвом» экране.

---

## 6.4. Техническая реализация и архитектура — 20%

### Уже реализовано хорошо

- modular monolith;
- Django apps по доменам;
- сервисный слой;
- integration adapter;
- tenant-aware архитектура;
- отдельные Student/Admin SPA;
- clear scaling path в `architecture.md`.

### Что нужно улучшить

#### A. `mvp_views.py` стал вторым приложением внутри config

В одном файле смешаны:

- demo constants;
- onboarding;
- courses/quizzes;
- opportunities;
- career;
- knowledge;
- admin analytics;
- CRUD.

Это противоречит уже заявленной архитектурной идее «thin views + domain services».

**Нужно:**

- перенести функции в соответствующие apps;
- либо хотя бы сократить `mvp_views.py` до compatibility facade;
- demo fixtures вынести отдельно.

#### B. `apps.zip` выглядит как отдельная/более старая копия части domain apps

Для сдачи должен быть **один source of truth**.

**Нужно:**

- не накладывать `apps.zip` поверх актуального `backend/apps` автоматически;
- проверить, есть ли в нем уникальный актуальный код;
- перенести только нужные изменения;
- удалить legacy/duplicate tree из финального submission.

#### C. Dead/mock frontend code

`Profile.tsx` содержит mock API, но активным маршрутом является упрощенный `ProfilePage.tsx`.

**Нужно:** объединить в одну рабочую реализацию и удалить/архивировать mock.

#### D. Несогласованность ролей

В проекте используются роли `student`, `editor`, `institute_admin`, `university_admin`, `mentor`, `organizer`, `admin`, а разные apps проверяют разные подмножества ролей.

**Нужно:** центральная RBAC matrix:

| Capability | student | editor | institute_admin | university_admin | organizer | admin |
|---|---:|---:|---:|---:|---:|---:|
| own profile | R/W | - | - | - | - | all |
| opportunities read | R | R | R | R | R | R |
| opportunities manage | - | according to scope | according to scope | tenant | tenant | all |
| knowledge manage | - | scoped | scoped | tenant | - | all |
| analytics | own/none | scoped | scoped | tenant | scoped | all |

Список должен быть упрощен до реально используемых в MVP ролей.

#### E. Notification status смешан с read state

Если `mark_read` переводит объект в sent, delivery и read semantics смешиваются.

**Нужно:**

- `delivery_status`;
- `sent_at`;
- `failed_at`;
- `read_at`;
- `provider_message_id`.

### Definition of Done

- один публичный API;
- один source of truth;
- отсутствуют неиспользуемые mock-экраны в critical path;
- доменная логика находится в services, а не в огромных views;
- архитектурная схема в README совпадает с фактическим кодом.

---

## 6.5. Безопасность, зависимости и работа с данными — 10%

## КРИТИЧНО: privilege escalation при регистрации

`UserRegistrationSerializer` принимает `role` от неавторизованного пользователя и допускает все значения из `User.ROLE_CHOICES`, включая:

- `editor`;
- `institute_admin`;
- `university_admin`;
- `organizer`;
- `admin`.

Публичный registration endpoint допускает unauthenticated registration.

Это означает, что в текущей логике клиент потенциально может зарегистрировать себе привилегированную роль.

### Исправление P0

Публичная регистрация должна жестко задавать:

```python
role = "student"
```

Привилегированные роли создаются только:

- через seed для demo;
- через Django admin;
- через admin-only endpoint;
- через invite flow.

Обязательно добавить тест:

```text
POST /register { role: "admin" }
→ создается student либо 400
→ административных прав нет
```

### Другие security actions

#### 1. Tenant isolation

Идея tenant filtering уже есть, но ее нужно закрепить тестами для **каждого публичного resource**.

Не стоит автоматически отправлять пользователя без university в `Demo University`: в production/testable flow tenant должен быть явным.

#### 2. Secrets

`.env.example` не содержит рабочего MAX token, это правильно.

Перед freeze:

- secret scan репозитория;
- убедиться, что `.env`, реальные tokens и service credentials отсутствуют;
- рабочие значения для проверки передавать через конкурсный канал/технический слайд, а не коммитить.

#### 3. DEBUG / hosts / CORS

Demo production environment:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<exact-hosts>
CORS_ALLOWED_ORIGINS=<exact-https-origins>
```

#### 4. JWT

Сейчас frontend хранит токен в `localStorage`. Для хакатона это может быть допустимым компромиссом, но необходимо:

- короткий access token;
- refresh flow;
- строгий CSP;
- отсутствие unsafe inline scripts, если возможно;
- явное описание ограничения в security notes.

#### 5. Rate limiting

Добавить throttling хотя бы для:

- login;
- register;
- knowledge search;
- bot/webhook endpoints.

#### 6. Personal data

Для demo использовать минимальные synthetic test profiles.

Не хранить:

- лишние персональные данные;
- чувствительные данные;
- реальные студенческие записи без необходимости.

README должен разделять:

- official/verified data;
- calculated result;
- recommendation;
- synthetic/demo data.

### Dependencies

Есть lock-файлы, но frontend Docker builder использует `npm install` вместо `npm ci`.

**Нужно:** заменить на `npm ci` для воспроизводимости.

Также `jsdom ^30.0.1` имеет более жесткие требования к Node, чем используемый `node:20-alpine`. Необходимо привести Docker Node version и devDependencies к одной поддерживаемой версии и прогнать `npm ci && npm test && npm run build` в той же версии Node, что используется в Docker/CI.

---

## 6.6. Техническая документация и комплектность — 10%

### Сейчас

Backend README содержит только базовый setup и список auth endpoints. Этого недостаточно для требований кейса.

Admin README уже содержит расхождение с кодом:

- README: `localhost:5174`, proxy `localhost:3000`;
- фактический `vite.config.ts`: порт `3001`, backend `8000`.

### Должен появиться единый top-level README

Обязательная структура:

```md
# <Product Name>

## 1. Назначение решения
## 2. Целевая аудитория
## 3. Основной пользовательский сценарий
## 4. Архитектура
## 5. Компоненты
## 6. Требования
## 7. Quick Start
   docker compose up --build
## 8. Переменные окружения
## 9. Порты
## 10. Зависимости
## 11. MAX integration
## 12. Работа с данными
## 13. Demo/test data
## 14. Test accounts
## 15. Пошаговая проверка сценария
## 16. Ожидаемый результат
## 17. API / OpenAPI
## 18. Запуск тестов
## 19. Известные ограничения
## 20. Остановка / повторный запуск
## 21. Что является mock/model data
## 22. Security notes
```

### Дополнительные обязательные/желательные файлы

```text
README.md
architecture.md
compose.yaml
.env.example
openapi.yaml
DATA-API.yaml
test-data/
  README.md
  seed.json / fixtures.json
scripts/
  smoke-test.sh
  demo-reset.sh
SECURITY.md
```

### DATA-API.yaml

Должен содержать минимум:

- schema/config version;
- solution/team ID;
- public base URL;
- обязательные checks;
- HTTP method;
- relative path;
- query/path/header/body params;
- test role;
- expected HTTP status;
- expected response content type/schema/required fields.

### Definition of Done

Новый проверяющий, не общаясь с командой, способен:

1. развернуть проект;
2. войти под тестовым пользователем;
3. пройти основной сценарий;
4. выполнить заявленные API checks;
5. увидеть ожидаемый результат;
6. понять, где mock, а где real integration.

---

# 7. Docker и воспроизводимость — обязательный P0

В переданных архивах есть Dockerfile отдельных компонентов, но **нет compose-файла**, который запускает решение целиком одной командой.

Рекомендуемая структура:

```text
project/
├── compose.yaml
├── .env.example
├── README.md
├── openapi.yaml
├── DATA-API.yaml
├── backend/
├── frontend-student/
├── frontend-admin/
├── docs/
│   └── architecture.md
├── test-data/
└── scripts/
```

Рекомендуемые services:

```text
postgres
backend
student-web
admin-web
```

Опционально:

```text
seed        # one-shot idempotent seed service
```

### Требования к compose

- Postgres healthcheck;
- backend ждет healthy DB;
- migrations выполняются автоматически;
- seed idempotent;
- frontend nginx проксирует `/api` на backend;
- внешний порт student/admin явно документирован;
- никакие секреты не вшиты в image;
- volumes используются только где действительно нужны;
- clean start с пустой БД воспроизводим.

### Команда из README

```bash
docker compose up --build
```

Дополнительные команды допускаются для разработки, но **основной demo запуск должен быть одной командой**.

---

# 8. OpenAPI и API quality

Поскольку решение имеет собственный REST API, для максимальной оценки API должен быть проверяемым контрактом.

## Нужно добавить

1. `openapi.yaml` OpenAPI 3.0/3.1.
2. Только реально используемые endpoints основного сценария.
3. Schemas request/response/error.
4. Bearer JWT auth scheme.
5. Examples.
6. Ошибочные status codes (`400`, `401`, `403`, `404`, `409`, `429`, `500/502/503` где применимо).
7. Test account roles.
8. CI validation OpenAPI.
9. `DATA-API.yaml` в формате конкурса.

## Минимальный обязательный набор API checks

```text
POST /api/auth/login/
POST /api/onboarding
GET  /api/student/career-gps
GET  /api/student/opportunities
POST /api/student/opportunities/{id}/save
GET/POST /api/student/subscriptions
GET  /api/knowledge/search?q=...
POST /api/admin/opportunities
GET  /api/admin/analytics
GET  /api/health/
```

После унификации paths список можно перенести в `/api/v1/...`.

---

# 9. Тестовая стратегия для максимума баллов

## 9.1. Уже есть

Backend tests:

- accounts;
- analytics;
- careers;
- knowledge;
- notifications;
- opportunities;
- profiles;
- subscriptions;
- smoke test основного набора backend endpoints.

Frontend tests:

- ProtectedRoute;
- CareerGPS;
- Knowledge;
- Opportunities;
- Admin Dashboard.

## 9.2. Что добавить

### P0 — e2e smoke

Один автоматический сценарий:

```text
seed demo
→ login student
→ onboarding
→ set skills
→ Career GPS
→ opportunities
→ save
→ subscription
→ login admin
→ publish matching opportunity
→ verify notification created
→ verify MAX mock/real provider contract
```

### P0 — authorization tests

- public user не может создать admin role;
- student не может вызвать admin CRUD;
- tenant A не видит tenant B;
- admin scope работает по заявленной модели.

### P1 — integration/error tests

- MAX timeout;
- MAX 401/429/500;
- retry;
- duplicate webhook;
- duplicate notification;
- malformed webhook;
- expired JWT;
- bad request body;
- DB constraint.

### P1 — frontend tests

- onboarding success/error;
- skills update;
- subscription flow;
- admin create opportunity error/retry;
- auth refresh;
- MAX launch context parsing.

### P1 — CI gate

```text
backend lint
backend tests
frontend student lint/test/build
frontend admin lint/test/build
OpenAPI validation
secret scan
Docker build
smoke test
```

---

# 10. Платформенный бонус MAX `+0,15`

## 10.1. Что не считать бонусом

Не рассчитывать на бонус только за:

- сам факт наличия mini-app;
- API;
- авторизацию;
- стандартную кнопку открытия приложения;
- просто большое число экранов;
- mock MAX client;
- обычный REST backend.

## 10.2. Рекомендуемая бонусная механика

### «Персональная подписка на карьерные возможности с проактивным уведомлением в MAX»

Сценарий:

1. Студент внутри mini-app выбирает тему/тип opportunity и создает подписку.
2. Администратор публикует подтвержденную opportunity.
3. `OpportunityMatchingService` / subscription matcher определяет релевантность.
4. Backend создает notification с idempotency key.
5. Реальный MAX bot отправляет пользователю сообщение.
6. Сообщение содержит поддерживаемое платформой действие, ведущее обратно в релевантный участок продукта.
7. Пользователь открывает opportunity и видит:
   - почему она ему подходит;
   - match score/reasons;
   - требования/gaps;
   - действие «сохранить» / дальнейший шаг.

### Почему это хороший бонус

- MAX используется не только как контейнер mini-app;
- пользователь получает ценность без постоянного ручного открытия приложения;
- механика органично продолжает уже реализованные subscriptions + matching + notifications;
- сценарий легко показать жюри от admin publish до получения сообщения;
- функциональность работает end-to-end и может быть описана/протестирована.

## 10.3. Что еще можно применить

Если актуальная документация MAX позволяет — использовать MAX Bridge для platform-aware поведения mini-app. Но сама по себе проверка `iOS/Android/desktop/web` не является достаточной пользовательской ценностью для бонуса. Она должна улучшать конкретное действие пользователя.

MAX UI можно использовать для нативного внешнего вида mini-app, но это следует считать усилением UX, а не единственным основанием бонуса.

## 10.4. Чеклист бонуса

- [ ] основной сценарий без бонуса полностью работает;
- [ ] используется реальная возможность MAX сверх обязательного mini-app входа;
- [ ] возможность дает измеримую пользовательскую ценность;
- [ ] backend event → MAX → пользователь → результат проходит полностью;
- [ ] есть fallback при недоступности MAX;
- [ ] есть idempotency;
- [ ] есть integration test;
- [ ] функция описана в README;
- [ ] функция показана в презентации/демо;
- [ ] для жюри подготовлен отдельный 30–60 секундный demo-flow.

---

# 11. Приоритетный backlog

## P0 — без этого нельзя сдавать как сильное MAX-решение

- [ ] Подключить реального MAX bot по актуальному API.
- [ ] Подключить mini-app к боту и публичному HTTPS URL.
- [ ] Реализовать связывание MAX identity ↔ local user.
- [ ] Сделать основной student flow полностью реальным от onboarding до результата.
- [ ] Подключить реальные skills/profile вместо dead mock implementation.
- [ ] Исправить privilege escalation через `role` при публичной регистрации.
- [ ] Создать top-level `compose.yaml`.
- [ ] Добиться запуска `docker compose up --build` на чистом окружении.
- [ ] Создать полноценный top-level `README.md`.
- [ ] Создать `openapi.yaml/json`.
- [ ] Создать `DATA-API.yaml`.
- [ ] Подготовить тестовые учетные записи и seed data.
- [ ] Исправить документационные расхождения портов.
- [ ] Убрать рабочие секреты из любых исходников и провести secret scan.
- [ ] Прогнать end-to-end smoke test перед freeze.

## P1 — чтобы претендовать на максимальные 3/3 по критериям

- [ ] Унифицировать `/api` и `/api/v1` contracts.
- [ ] Использовать admin endpoint для admin opportunities list.
- [ ] Централизовать RBAC.
- [ ] Покрыть tenant isolation негативными тестами.
- [ ] Добавить JWT refresh flow.
- [ ] Сделать единый API error envelope.
- [ ] Убрать `str(e)` из пользовательских API ответов.
- [ ] Подключить retry MAX deliveries.
- [ ] Добавить idempotency notification/webhook.
- [ ] Разнести delivery/read notification status.
- [ ] Добавить user-visible error/retry во всех critical screens.
- [ ] Вынести demo datasets из `mvp_views.py`.
- [ ] Удалить dead mocks/duplicate source tree.
- [ ] `npm ci` вместо `npm install` в Docker builder.
- [ ] Согласовать Node version и `jsdom` requirements.
- [ ] Добавить throttling auth/search/webhook.
- [ ] Добавить CSP/security headers на frontend reverse proxy.

## P2 — усиление качества перед финалом

- [ ] Structured logging + correlation/request ID.
- [ ] Metrics: errors, MAX delivery rate, API latency.
- [ ] Sentry/аналог при возможности.
- [ ] Architecture Decision Records для 2–3 ключевых решений.
- [ ] Load smoke на главные endpoints.
- [ ] DB indexes по частым tenant/status/filter полям.
- [ ] Улучшить admin audit trail.
- [ ] Удалить `db.sqlite3`, `__pycache__` и прочие runtime artifacts из submission.

## BONUS — после P0

- [ ] Subscription → publish → real MAX notification → открыть opportunity → сохранить.
- [ ] Описать эту механику как отдельную платформенную функцию.
- [ ] Доказать ее ценность и end-to-end работу на защите.

---

# 12. Рекомендуемая целевая архитектура submission

```text
MAX Bot
   │
   ├── команды / уведомления / entry point
   │
   └── открывает MAX Mini App
              │
              ▼
       React Student UI
              │
              ▼
        Django REST API
        ├── Accounts / RBAC
        ├── Profiles / Skills
        ├── Career GPS
        ├── Opportunity Matching
        ├── Subscriptions
        ├── Knowledge
        ├── Notifications
        ├── Analytics
        └── MAX Adapter
              │
              ├── PostgreSQL
              └── MAX Bot API

React Admin UI ──────► Django REST API
```

Ключевой принцип: MAX integration должна быть полноценным boundary-domain, но не должна разносить MVP на микросервисы.

---

# 13. Что сознательно НЕ нужно делать до закрытия P0/P1

Чтобы не потерять время и не снизить качество основного сценария, пока не нужно:

- добавлять новые образовательные модули;
- расширять quiz/course функциональность;
- строить сложную ML/LLM систему только ради «AI»;
- выделять микросервисы;
- добавлять Redis/Celery, если retry можно надежно закрыть более простой схемой MVP;
- делать десятки новых endpoints;
- усложнять роли, если для демо достаточно student + university_admin;
- добавлять функции, которые нельзя показать end-to-end.

Максимум технических баллов здесь даст не число функций, а **работающий и воспроизводимый сценарий + реальная MAX интеграция + безопасность + тесты + документация**.

---

# 14. Финальный технический Definition of Done

## Admission / MAX

- [ ] Бот MAX отвечает.
- [ ] Mini-app открывается из MAX.
- [ ] Основной сценарий доступен в MAX web/mobile в предусмотренном кейсом объеме.
- [ ] HTTPS сертификат валиден.
- [ ] Нет зависимости от локального компьютера участника.

## Main scenario

- [ ] Новый test student может пройти onboarding.
- [ ] Его skills/interests/goal реально сохраняются.
- [ ] Career GPS строится по сохраненным данным.
- [ ] Opportunities ранжируются с объяснением.
- [ ] Opportunity можно сохранить.
- [ ] Subscription можно создать.
- [ ] Admin может создать/опубликовать opportunity.
- [ ] Подходящая subscription вызывает MAX notification.
- [ ] Пользователь возвращается из MAX к нужному результату.

## Reliability

- [ ] Повторный сценарий не ломает состояние.
- [ ] Есть понятные loading/error/success states.
- [ ] Временная ошибка MAX не ломает приложение.
- [ ] Retry не создает duplicate notifications.
- [ ] JWT refresh работает.
- [ ] Нет систематических 500/timeout.

## Security

- [ ] Нельзя self-register admin/privileged role.
- [ ] Tenant isolation покрыт тестами.
- [ ] Admin endpoints защищены.
- [ ] Secrets отсутствуют в git/archive.
- [ ] DEBUG=false в публичной среде.
- [ ] CORS/hosts ограничены.
- [ ] Webhook/auth endpoints имеют validation/throttling.

## Reproducibility

- [ ] `docker compose up --build` работает на чистой машине.
- [ ] Сборка укладывается в лимит кейса.
- [ ] Seed выполняется воспроизводимо.
- [ ] Все dependency versions зафиксированы.
- [ ] Node/Docker versions согласованы.

## API

- [ ] Public HTTPS API доступен.
- [ ] `openapi.yaml/json` валиден.
- [ ] `DATA-API.yaml` заполнен.
- [ ] Test accounts работают.
- [ ] Test data приложены.
- [ ] status codes и schemas соответствуют контракту.

## Documentation

- [ ] README содержит все пункты кейса.
- [ ] Архитектура актуальна.
- [ ] Описаны реальные и модельные интеграции.
- [ ] Описаны data sources / freshness / demo data.
- [ ] Есть пошаговая проверка.
- [ ] Есть expected result.
- [ ] Есть known limitations.
- [ ] Зафиксирован commit hash / checksum.

## Platform bonus

- [ ] Реальная дополнительная MAX-функция работает end-to-end.
- [ ] Ее пользовательская ценность понятна без объяснений разработчика.
- [ ] Она описана в README.
- [ ] Она показана в презентации.

---

# 15. Рекомендуемый порядок выполнения

```text
1. Security P0: registration/RBAC
2. Consolidate one API/source-of-truth
3. Finish profile/skills → Career GPS → opportunities flow
4. Real MAX bot + mini-app launch
5. Real MAX notification path
6. Docker Compose + clean seed
7. OpenAPI + DATA-API
8. Error handling + JWT refresh + idempotency
9. E2E tests
10. README + test instructions
11. Platform bonus demo
12. Freeze commit / checksum
13. Final clean-machine rehearsal
```

Если время ограничено, пункты 1–7 важнее появления любых новых функций.

---

# 16. Итог

Текущий проект уже имеет сильную backend-базу: modular monolith, сервисный слой, Career GPS, explainable matching, knowledge search, subscriptions, analytics и abstraction для MAX. Это позволяет не переписывать MVP с нуля.

Чтобы превратить заготовку в конкурсное решение, основной объем работы нужно направить не на расширение функционала, а на **доведение существующих компонентов до одного доказуемого end-to-end MAX-сценария**, устранение security gap, воспроизводимый Docker запуск, формальный API contract, обработку ошибок и полный комплект технической документации.

Самая рациональная дополнительная функция для платформенного бонуса — **проактивное персональное уведомление о релевантной карьерной возможности через MAX с возвратом пользователя в конкретный результат mini-app**. Она почти полностью опирается на уже реализованные matching, subscriptions и notification services и поэтому дает высокое соотношение «ценность / объем доработки».

---

## Источники анализа

- `Образовательные решения.pdf`, стр. 9–10 — формат сдачи и требования к собственному API.
- `Образовательные решения.pdf`, стр. 13 — технические критерии и платформенный бонус.
- `Образовательные решения.pdf`, стр. 15 — возможности MAX: Bot API, MAX Bridge, MAX UI, mini-app.
- `architecture.md` — заявленная архитектура проекта.
- `backend.zip`, `frontend-student.zip`, `frontend-admin.zip`, `apps.zip` — статический аудит текущей реализации.

### Ограничение аудита

Документ составлен по переданным исходникам и статическому анализу. Наличие production MAX credentials, реально опубликованного mini-app и работающего публичного API из исходников подтвердить нельзя. Перед сдачей требуется отдельная clean-environment проверка фактического deploy и полного сценария в MAX.
