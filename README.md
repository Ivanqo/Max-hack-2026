# UniPath MAX — описание проекта и инструкция по запуску

UniPath MAX — прототип цифрового карьерного навигатора для студентов строительного вуза. Этот README объединяет краткое описание решения, проверяемый статус проекта, локальный запуск и подготовку production-стенда. Пароли, токены, webhook-секреты и персональные данные здесь не публикуются.

## Задача и ценность

Целевая аудитория — студенты, которым трудно выбрать карьерное направление, понять, каких навыков не хватает, и найти подходящую практику или проект; второй пользователь — вузовский администратор, который публикует и поддерживает актуальность возможностей и справочной информации. Прототип связывает профиль и навыки студента с карьерными ролями, возможностями, подписками и материалами базы знаний, а администраторам дает интерфейс управления содержимым.

Основание для гипотезы — сведения команды о 15 интервью со студентами НИУ МГСУ: 10 студентов 4-го курса, 3 — 3-го курса и 2 — 1-го курса. В этой выборке 8 из 15 не определились с конечным направлением, 3 из 15 затруднились назвать нужные навыки, а 4 из 15, по оценке команды, занижали свои навыки и не решались воспользоваться возможностями. Участники также говорили, что сложно найти оплачиваемую практику по специальности. Оценка покрытия практикой примерно 20–40% потока звучала как мнение участников о наблюдениях руководителей практики, а не как официальная статистика. Выборка небольшая и не является измерением распространенности проблемы среди всех студентов.

## Пользовательские контуры и функциональный статус

- **Студенческий контур:** регистрация/вход, профиль и навыки, Career GPS по карьерным ролям, каталог и карточки возможностей, сохранение возможностей, подписки на темы и поиск по базе знаний. Уведомления доступны через API; отдельного центра уведомлений в интерфейсе студента нет. Вход из MAX Mini App зависит от реальной настройки приложения и подписанных `initData`; браузерный локальный запуск не заменяет этот путь.
- **Административный контур:** отдельная SPA с аналитической сводкой и управлением возможностями, карьерными ролями и базой знаний. Раздел пользователей позволяет просматривать учетные записи и профиль студента, а также менять активность; доступ ограничен текущими правами backend. Публичная регистрация создает студенческие учетные записи; администратора боевого стенда создает оператор вручную.

Текущая модель возможностей не содержит отдельного структурированного поля оплаты. Поэтому фильтр или подтвержденный подбор именно оплачиваемой практики не заявляется. Seed-данные синтетические; это демонстрационный набор, не выгрузка из информационных систем вузов и не актуальный каталог вакансий.

## Архитектура

```text
MAX Mini App / браузер -> внешний TLS reverse proxy
                              |
                     frontend-student Nginx
                       /       |        \\
             /api -> backend   /admin/ -> frontend-admin
                    |
              PostgreSQL 15

backend -> MAX Bot API: mock по умолчанию / real по настройке
```

Оба frontend-приложения написаны на React, TypeScript и Vite; backend — Django 5, Django REST Framework и JWT; хранилище — PostgreSQL 15. Docker Compose собирает четыре сервиса: БД, API, студенческий frontend и административный frontend. Внешний TLS reverse proxy разворачивается отдельно. Подробные схемы и модули приведены ниже.

## Пилот и подтвержденные результаты

По сведениям команды, МГСУ согласовал тестовый пилот для студентов Института цифровых технологий и моделирования в строительстве. Университет готов информировать студентов, размещать возможности и пополнять базу знаний. Сроки, размер тестовой группы и владельцы данных пока не уточнены; подтверждение и план пилота не приложены в репозитории.

Измеренных продуктовых результатов пока нет. Есть интервью и технические прогоны. В ручном MAX-сценарии сообщение появилось в тестовом диалоге; переход к карточке сработал после закрытия Mini App, а первый переход без закрытия оставил прежний экран. Переключение привязки МГСУ/МАИ при входе и число доставленных получателей не подтверждены. Mock-режим не проверяет реальную доставку MAX. Не заявляются полностью проверенная MAX-интеграция, достигнутый бонус или максимальный балл.

## Требования

- Docker Engine или Docker Desktop с Docker Compose — для полного локального запуска;
- Node.js 20 и npm — только если запускать Vite-интерфейсы отдельно от Docker;
- Python 3.11 — если запускать Django-команды вне контейнера.

## Быстрый запуск

Из корня репозитория создайте локальный `.env` и запустите стек:

```powershell
Copy-Item .env.example .env
```

Перед запуском заполните в `.env` `DB_PASSWORD`, `DATABASE_URL` и `DJANGO_SECRET_KEY`: шаблон намеренно не содержит готовых паролей или ключей. Для DB password используйте значение, сгенерированное `openssl rand -hex 32`, и укажите тот же пароль в `DATABASE_URL`; для Django key можно сгенерировать `openssl rand -hex 48`. В Linux/macOS сначала выполните `cp .env.example .env`. Значения из локального `.env` не переносите в публичные материалы.

```powershell
docker compose up --build -d
```

Compose запускает PostgreSQL, Django API и два frontend-сервиса. Backend ожидает готовности БД, применяет миграции и при `AUTO_SEED_DEMO=true` загружает демонстрационные данные. Порты по умолчанию привязаны к `127.0.0.1`: интерфейсы доступны на этой машине, но напрямую не публикуются во внешнюю сеть.

| Сервис | Локальный адрес | Настройка порта |
| --- | --- | --- |
| Student frontend | `http://localhost:3000` | `STUDENT_PORT` |
| Admin frontend | `http://localhost:3001` | `ADMIN_PORT` |
| Django API health | `http://localhost:8000/api/health/` | `BACKEND_PORT` |
| PostgreSQL | `localhost:5432` | порт в `docker-compose.yml` |

`BACKEND_PORT`, `STUDENT_PORT` и `ADMIN_PORT` задают привязку хоста и порт, например `127.0.0.1:8000`. Не привязывайте эти сервисы к внешнему интерфейсу сервера: публичный HTTPS-трафик должен входить через настроенный reverse proxy.

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

## Развёртывание боевого стенда

Корневой Compose-файл собирает production-образы по умолчанию. Для публичного стенда дополнительно нужны Linux-сервер с Docker Engine и Compose plugin, доменное имя с DNS-записью на сервер и TLS reverse proxy. Откройте во внешнем firewall только необходимые порты SSH, HTTP и HTTPS; PostgreSQL и сервисные порты приложений оставьте доступными только на loopback.

### 1. Получите код на сервере

```bash
git clone --branch main https://github.com/Ivanqo/Max-hack-2026.git /opt/unipath-max
cd /opt/unipath-max
cp .env.example .env
chmod 600 .env
```

Установите Docker Engine и Compose plugin по [официальной инструкции Docker Engine](https://docs.docker.com/engine/install/) и [инструкции Compose plugin для Linux](https://docs.docker.com/compose/install/linux/). В репозитории нет скрипта установки Docker или настройки firewall сервера.

### 2. Заполните production `.env`

Сгенерируйте новые значения для секрета Django и пароля PostgreSQL, например `openssl rand -hex 48` и `openssl rand -hex 32`. В `.env` замените значения как минимум для:

```env
DB_PASSWORD=<новый hex-пароль>
DATABASE_URL=postgresql://maxhack_user:<тот-же-hex-пароль>@db:5432/maxhack
DJANGO_SECRET_KEY=<новый секрет>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=app.example.org,localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=https://app.example.org
BACKEND_PORT=127.0.0.1:8000
STUDENT_PORT=127.0.0.1:3000
ADMIN_PORT=127.0.0.1:3001
BUILD_TARGET=production
AUTO_SEED_DEMO=false
MAX_INTEGRATION_MODE=mock
MAX_WEBAPP_BASE_URL=https://app.example.org/
```

Замените `app.example.org` на свой домен. Значение пароля в `DATABASE_URL` должно совпадать с `DB_PASSWORD`; используйте URL-безопасный пароль или URL-кодируйте специальные символы. `AUTO_SEED_DEMO=false` обязателен для production: seed создает тестовые учетные записи с известными паролями и синтетические записи. Секреты не сохраняйте в Git.

### 3. Настройте HTTPS reverse proxy

DNS домена должен указывать на сервер; входящие 80/443 должны быть доступны reverse proxy. Внешний TLS-прокси должен терминировать HTTPS и направлять запросы на `http://127.0.0.1:3000`. Frontend Nginx внутри Compose уже проксирует `/api/` к Django и `/admin/` к административному frontend.

Пример Caddyfile для простого стенда:

```caddyfile
app.example.org {
    reverse_proxy 127.0.0.1:3000
}
```

Caddy может автоматически получать и обновлять публичный сертификат, если домен резолвится на сервер и порты 80/443 доходят до Caddy. См. [официальное руководство Caddy по reverse proxy](https://caddyserver.com/docs/quick-starts/reverse-proxy) и [Automatic HTTPS](https://caddyserver.com/docs/automatic-https). Альтернативный `deploy/nginx/188-120-251-143.sslip.io.conf` в этом репозитории только перенаправляет HTTP на HTTPS: он не настраивает TLS-сертификат и upstream. Не запускайте одновременно два edge-прокси, претендующих на одни и те же порты.

### 4. Соберите и запустите Compose

```bash
export BUILD_COMMIT_SHA="$(git rev-parse --short HEAD)"
docker compose config -q
docker compose up --build -d
docker compose ps
```

Compose применит миграции перед запуском Gunicorn. После старта проверьте локальный health endpoint и внешний HTTPS-маршрут:

```bash
curl -fsS http://127.0.0.1:8000/api/health/
curl -fsS https://app.example.org/api/health/
```

Откройте `https://app.example.org/` и `https://app.example.org/admin/`. Логи контейнеров доступны на сервере через `docker compose logs -f backend` и `docker compose logs -f frontend-student`.

### 5. Создайте административную учетную запись

Так как демо-seed выключен и публичная регистрация создает только студенческие учетные записи, создайте университетского администратора вручную. Откройте Django shell:

```bash
docker compose exec backend python manage.py shell
```

В интерактивной оболочке создайте пользователя с ролью `admin` и названием университета, совпадающим с областью данных:

```python
from getpass import getpass
from django.contrib.auth import get_user_model

get_user_model().objects.create_user(
    email=input("Email: ").strip(),
    password=getpass("Password: "),
    role="admin",
    university=input("University name: ").strip(),
)
```

Это создает tenant-администратора без `is_superuser`, обходящего изоляцию университетов. Не используйте seed-аккаунты в боевом окружении.

### 6. Включите MAX API при необходимости

Публичный стенд можно сначала запустить с `MAX_INTEGRATION_MODE=mock`. Для реальной доставки настройте в `.env`:

```env
MAX_INTEGRATION_MODE=real
MAX_API_URL=https://platform-api2.max.ru
MAX_BOT_TOKEN=<секретный-токен-бота>
MAX_WEBHOOK_SECRET=<случайный-секрет-из-букв-цифр-дефисов-и-подчеркиваний>
MAX_WEBHOOK_URL=https://app.example.org/api/max/webhook/
MAX_OPEN_APP_TARGET=https://max.ru/<bot_username>
MAX_WEBAPP_BASE_URL=https://app.example.org/
```

Значения в угловых скобках замените реальными секретами только на сервере; не помещайте их в README, Git или клиентский код. После запуска зарегистрируйте webhook:

```bash
docker compose exec backend python manage.py register_max_webhook
```

Для реальной доставки необходимы публичный HTTPS, действующие реквизиты бота, доступный webhook и привязанный MAX-профиль получателя. Успешный локальный mock не подтверждает доставку через MAX.

### Обновление и резервная копия

Перед обновлением создайте резервную копию PostgreSQL вне каталога репозитория. Пример для значений по умолчанию `DB_USER=maxhack_user` и `DB_NAME=maxhack`:

```bash
install -d -m 700 /var/backups/unipath-max
docker compose exec -T db pg_dump -U maxhack_user maxhack \
  > "/var/backups/unipath-max/$(date +%F_%H%M%S).sql"
```

Обновите checkout из `main`, затем пересоберите контейнеры:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
export BUILD_COMMIT_SHA="$(git rev-parse --short HEAD)"
docker compose up --build -d
docker compose ps
```

Миграции применяются при старте backend. Перед откатом к старому коду учитывайте, что обратная совместимость миграций отдельно не гарантируется; сохраняйте дамп БД и проверяйте план восстановления для конкретной версии.

## Seed и демонстрационные данные

Команда `python manage.py seed_demo` доступна из каталога `backend/`. В Docker она вызывается при старте, если `AUTO_SEED_DEMO=true` (значение в `.env.example`). Команда идемпотентно создает или обновляет тестовые записи для двух университетских контекстов: пользователей, профили, навыки, карьерные роли, возможности, материалы базы знаний и подписки. Это синтетические данные, не выгрузка из систем МГСУ или МАИ.

Seed печатает учетные данные синтетических demo-пользователей в журнал backend; в README сами пароли не приводятся. Используйте эти записи только в локальной демонстрационной базе, не переносите журналы с учетными данными в публичные материалы и не включайте `AUTO_SEED_DEMO` на production-стенде. Для доступа проверяйте локальный вывод seed или используйте учетные данные, переданные проверяющим по защищенному каналу:

```powershell
docker compose logs backend
```

Для запуска seed вручную в работающем контейнере:

```powershell
docker compose exec backend python manage.py seed_demo
```

### Проверка интерфейсов на локальных данных

1. Откройте `http://localhost:3000` и войдите под тестовым студентом из локального seed; его учетные данные доступны только в локальном seed-выводе или через защищенный канал проверки.
2. Проверьте доступность профиля, Career GPS, списка и карточки возможностей, подписок и базы знаний.
3. Откройте `http://localhost:3001`, войдите под тестовой административной учетной записью и создайте активную возможность с требованиями, совпадающими с темой подписки студента.
4. После публикации административный интерфейс покажет сводку уведомлений. В mock-режиме ожидаемый статус — `simulated`; реальное сообщение MAX этим не подтверждается. Сами записи студента можно прочитать через `GET /api/v1/notifications/` с его JWT.
5. Для проверки публичного MAX launch нужен запуск из настроенного бота, который передает подписанные `initData`; локальный браузерный запуск этого контекста не создает.

API-сценарий, который создает и затем удаляет свои тестовые записи, описан отдельно в разделе «API и схемы» ниже.

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

Полная OpenAPI 3.0.3 спецификация находится в [`openapi.yaml`](openapi.yaml), а проверки API для формата сдачи — в [`DATA-API.yaml`](DATA-API.yaml). Последний задает публичный base URL `https://188-120-251-143.sslip.io`; его health endpoint ответил HTTP 200 на 27 сентября 2026 года, однако сервис сообщил `build_commit: null`, поэтому соответствие развернутого кода текущему `main` отдельно не подтверждено. API и schema не заменяют ссылку для запуска Mini App внутри MAX.

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

## Проверка формата сдачи

README и дерево проекта сверены с разделами о сдаче технического решения и презентации PDF в кейсе «Образовательные решения» (стр. 9–10; критерии допуска и оценки — стр. 11–13). Инструкции кейса перечислены здесь как контрольные требования, а не как подтверждение фактически полученных результатов.

| Требование к материалам | Что есть в репозитории / статус |
| --- | --- |
| Исходный код и фиксированная версия | Код находится в Git-репозитории [Ivanqo/Max-hack-2026](https://github.com/Ivanqo/Max-hack-2026); сдаваемую версию фиксируйте commit hash из `git rev-parse HEAD` на `main`. Публичный API сейчас не сообщает commit hash развернутого backend. |
| README: назначение, сценарий, состав, запуск, параметры, данные, проверки, поведение, ограничения и остановка | Описаны в этом файле; локальный запуск требует заполнить `.env`, затем выполняется одной командой `docker compose up --build -d`. Команды сверены с compose, Dockerfiles и manifest-файлами; тестовые наборы в рамках этой проверки не запускались. |
| Docker и зависимости | В репозитории есть корневой `docker-compose.yml`, Dockerfile и `.dockerignore` для сервисов, `.env.example`, `backend/requirements.txt`, `package.json` и lock-файлы обоих frontend. В `.env.example` нет готовых значений паролей, ключей или MAX-токенов. |
| API и технический сценарий | Есть `openapi.yaml` (OpenAPI 3.0.3), `DATA-API.yaml` и [`DEMO_TEST_SCENARIO.md`](DEMO_TEST_SCENARIO.md). В `output/reports` сохранены результаты schema validation и локального smoke-сценария в mock-режиме; это отчеты прошлых прогонов, не повторная проверка в этом аудите. |
| Доступ к решению из MAX | Полный MAX-сценарий не подтвержден: частичный ручной результат описан выше. Проверяемая публичная ссылка на Mini App и гарантированная доставка сообщения не подтверждены. Тестовые учетные данные для проверяющих передаются отдельно и защищенно; в README они не включаются. |
| Презентация PDF | В репозитории есть материалы презентации в DOCX, но PDF презентации для сдачи среди отслеживаемых файлов нет. До отправки заявки требуется подготовить и проверить PDF; его первый технический слайд должен содержать MAX entry link, ссылку на Git-репозиторий и commit hash, API link, сведения о тестовом доступе/конфигурации и короткий проверочный сценарий. Пароли и рабочие токены передавайте только предусмотренным организаторами защищенным способом. Остальные слайды должны покрыть пункты презентационного формата из кейса: проблема и целевая аудитория, executive summary, решение и пользовательский сценарий, команда, рынок, модель и план масштабирования, пилот/партнерства, экономика/ресурсы, риски и развитие. |
| Сборка не дольше 5 минут | В кейсе задан такой предел без времени скачивания базовых образов. Время сборки этого репозитория не измерено, соответствие пока не подтверждено. |
| Пилот, эффекты и источники | Сведения команды о пилоте и интервью изложены выше с оговорками. Измеренных продуктовых эффектов и согласованных сроков/размера группы/владельцев данных пока нет. |

Для официальной подачи дополнительно сверьте актуальную редакцию конкурсного PDF: сам файл кейса, презентационный PDF, MAX entry link и проверочные учетные данные не являются заменой друг другу.

## Технические ограничения

- Отдельного поля оплаты в модели возможности нет.
- Уведомления доступны через backend API; отдельного центра уведомлений в student frontend нет.
- Реальная доставка зависит от конфигурации MAX и привязки MAX ID к профилю.
- Поиск базы знаний выполняется по подготовленным записям; seed-данные синтетические.
- Frontend refresh-flow для JWT ограничен; подробности ведутся в `SECURITY.md`.

Дополнительные инструкции: [DOCKER.md](DOCKER.md), [docs/architecture.md](docs/architecture.md), [SECURITY.md](SECURITY.md). Источник требований формата — кейс «Образовательные решения.pdf», стр. 9–13; в репозитории он не хранится.
