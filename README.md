# SkillPath Navigator

Рекомендательная система обучения для разработчиков. Пользователь описывает свои навыки (в том числе свободным текстом — разбирается через LLM), система строит граф зависимостей между навыками, рекомендует следующие шаги, строит оптимальный путь обучения и подсказывает где искать материалы (GitHub, YouTube, курсы).

## Содержание

- [Стек](#стек)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Запуск локально](#запуск-локально)
- [Запуск на удалённом сервере](#запуск-на-удалённом-сервере)
- [REST API](#rest-api)
- [GraphQL](#graphql)
- [WebSocket](#websocket)
- [Мониторинг](#мониторинг)
- [Тесты и линтинг](#тесты-и-линтинг)
- [CI/CD](#cicd)
- [Make-команды](#make-команды)

---

## Стек

| Слой | Технологии |
|---|---|
| Фреймворк | Django 4.2, Django REST Framework 3.14 |
| Аутентификация | JWT (simplejwt 5.3.1) + Argon2 + blacklist при ротации |
| API | REST (DRF) + GraphQL (graphene-django) |
| Real-time | Django Channels 4 + WebSocket |
| ASGI-сервер | Gunicorn + Uvicorn workers |
| Граф навыков | Neo4j 5 (прод) / networkx in-memory (dev/тесты) |
| База данных | PostgreSQL 15 / SQLite (dev/тесты) |
| Кэш | Redis 7 (django-redis) |
| Очередь задач | Celery 5 + Redis broker (async LLM-анализ) |
| LLM | Anthropic Claude claude-sonnet-4-6 (с поддержкой MCP) |
| Внешние API | GitHub, YouTube, Stepik, Coursera (мок без ключей) |
| Документация | drf-spectacular (OpenAPI 3.0 + Swagger UI) |
| Фронтенд | React 18 + Vite 5 + Tailwind CSS + vis-network |
| Прокси | nginx (reverse proxy + раздача статики из shared volume) |
| Мониторинг | Prometheus (/metrics/) + Flower (Celery dashboard) |
| Логирование | JSON-логи в production (python-json-logger) |
| Трекинг ошибок | Sentry (опционально, через `SENTRY_DSN`) |

---

## Архитектура

```
Браузер
  │
  ▼
┌─────────────────────────────────────┐
│  nginx (порт 80 / 443)              │
│  /           → React SPA            │
│  /api/       → gunicorn :8000       │
│  /admin/     → gunicorn :8000       │
│  /graphql/   → gunicorn :8000       │
│  /ws/        → gunicorn :8000       │
│  /metrics    → только Docker-сеть   │
│  /static/    → shared volume        │
└────────────────┬────────────────────┘
                 │
  ┌──────────────▼───────────────────────────────────┐
  │  Gunicorn + UvicornWorker (ASGI)                 │
  │  apps/api               — REST (health/ready)    │
  │  apps/skills/views.py   — навыки + граф          │
  │  apps/progress/views.py — прогресс + пути        │
  │  apps/recommendations/  — LLM + Celery polling   │
  │  apps/resources/views.py — GitHub/YouTube/курсы  │
  │  apps/graphql_schema    — GraphQL                │
  │  apps/progress.consumers — WebSocket (Channels)  │
  └───────────┬────────────────────┬─────────────────┘
              │                    │
  ┌───────────▼──────┐  ┌─────────▼──────────────────┐
  │  PostgreSQL 15   │  │  Redis 7                   │
  │  (основная БД)   │  │  кэш + channel layer       │
  └──────────────────┘  │  Celery broker (DB 2)      │
              │          │  Celery results (DB 3)     │
  ┌───────────▼──────┐  └──────────┬─────────────────┘
  │  Neo4j 5         │             │
  │  (граф навыков)  │  ┌──────────▼──────────────────┐
  │  --profile neo4j │  │  Celery Worker              │
  └──────────────────┘  │  analyze_skills_text_task   │
                         └─────────────────────────────┘

core/
  constants.py  — SKILL_LEVELS, RELATION_TYPES, ключи кэша
  middleware.py — JWTAuthMiddleware для WebSocket
  pagination.py — StandardPagination (20 / макс. 100)
  permissions.py — IsAdminOrReadOnly, IsOwnerOrAdmin
  throttles.py  — LoginRateThrottle (10/hour на /token/)
```

---

## Структура проекта

```
skillpath_navigator/
├── .github/workflows/ci.yml      # test → lint → mypy → docker-build → publish
├── .pre-commit-config.yaml       # black, isort, flake8
├── Makefile
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh             # migrate → collectstatic → superuser → seed → gunicorn
│   ├── pytest.ini                # coverage gate 60%
│   ├── config/
│   │   ├── settings.py
│   │   ├── celery.py             # Celery app init
│   │   └── urls.py
│   ├── core/
│   │   ├── constants.py
│   │   ├── middleware.py
│   │   ├── pagination.py
│   │   ├── permissions.py
│   │   └── throttles.py          # LoginRateThrottle
│   ├── apps/
│   │   ├── api/                  # urls.py + views.py (health/readiness)
│   │   ├── users/                # модели, сериализаторы, views, urls
│   │   ├── skills/               # модели, views, signals, filters
│   │   ├── graph/                # GraphService (Neo4j/networkx)
│   │   ├── progress/             # модели, views, WebSocket consumers
│   │   ├── recommendations/      # LLM, Celery tasks, views
│   │   ├── resources/            # GitHub, YouTube, курсы, views
│   │   └── graphql_schema/       # GraphQL схема
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── factories.py          # UserFactory, SkillFactory, UserSkillFactory
│   │   ├── test_api.py
│   │   ├── test_tasks.py         # Celery tasks, rate-limit, concurrency
│   │   └── ...
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
└── frontend/
    ├── Dockerfile                # multi-stage: node build → nginx
    ├── nginx.conf                # reverse proxy + /metrics ограничен сетью
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx               # JWT auto-refresh при 401 (через api.js)
        ├── api.js                # fetch + auto-refresh + Celery polling
        └── components/
            ├── Auth.jsx
            ├── Dashboard.jsx
            ├── SkillGraph.jsx    # vis-network граф
            ├── LearningPath.jsx
            ├── Resources.jsx
            └── Progress.jsx
```

---

## Запуск локально

### Требования

- Python 3.11+
- Node.js 20+ и npm
- (опционально) Docker + Docker Compose — для PostgreSQL, Redis, Neo4j

### Вариант А — полностью без Docker (SQLite + in-memory граф)

```bash
# 1. Клонировать репозиторий
git clone <url> skillpath_navigator
cd skillpath_navigator

# 2. Настроить окружение бэкенда
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Скопировать и проверить .env
cp .env.example ../.env
# DB_NAME оставить пустым → SQLite
# GRAPH_BACKEND=memory           → граф в памяти (не требует Neo4j)
# USE_REDIS_CACHE=false          → кэш в памяти (не требует Redis)
# USE_MOCK_EXTERNAL_APIS=True    → моки вместо реальных GitHub/YouTube API

# 4. Создать БД и таблицы
python manage.py migrate

# 5. Создать администратора
python manage.py createsuperuser

# 6. Наполнить каталог навыков
python manage.py seed_skills

# 7. Запустить бэкенд
python manage.py runserver
# → http://localhost:8000/api/v1/
# → http://localhost:8000/admin/
# → http://localhost:8000/api/docs/   (Swagger UI)
```

```bash
# В отдельном терминале — запустить фронтенд
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

> **Без каких ключей всё равно работает:**
> БД — SQLite, граф — in-memory, LLM — эвристика, внешние API — моки.

---

### Вариант Б — бэкенд с Docker (PostgreSQL + Redis), Django локально

```bash
# Поднять только инфраструктуру
docker compose up postgres redis -d

# Настроить .env
cat > .env << 'EOF'
SECRET_KEY=dev-secret-change-in-prod
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=skillpath_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
USE_REDIS_CACHE=True

GRAPH_BACKEND=memory
USE_MOCK_EXTERNAL_APIS=True
DJANGO_LOG_LEVEL=INFO
EOF

# Запустить бэкенд
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_skills
python manage.py runserver

# В отдельном терминале — Celery worker (для LLM-задач)
celery -A config worker --loglevel=info
```

---

### Переменные окружения (справочник)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `SECRET_KEY` | insecure dev key | Обязательно сменить в production |
| `DEBUG` | `True` | `False` в production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Домены сервера через запятую |
| `DB_NAME` | _(пусто → SQLite)_ | Имя базы PostgreSQL |
| `DB_USER` | `postgres` | Пользователь PostgreSQL |
| `DB_PASSWORD` | `postgres` | Пароль PostgreSQL |
| `DB_HOST` | `localhost` | Хост PostgreSQL |
| `DB_CONN_MAX_AGE` | `60` | Пул соединений с БД (секунды) |
| `GRAPH_BACKEND` | `memory` | `memory` или `neo4j` |
| `NEO4J_URI` | `bolt://localhost:7687` | Адрес Neo4j |
| `NEO4J_PASSWORD` | `password` | Пароль Neo4j |
| `REDIS_HOST` | `localhost` | Хост Redis |
| `USE_REDIS_CACHE` | `True` | `false` для тестов без Redis |
| `ANTHROPIC_API_KEY` | _(пусто)_ | Ключ Claude API |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Модель Claude |
| `LLM_THROTTLE_RATE_PER_HOUR` | `10` | Лимит LLM-запросов на пользователя |
| `GITHUB_TOKEN` | _(пусто)_ | Токен GitHub API |
| `YOUTUBE_API_KEY` | _(пусто)_ | Ключ YouTube Data API |
| `STEPIK_TOKEN` | _(пусто)_ | Токен Stepik API |
| `USE_MOCK_EXTERNAL_APIS` | `True` | Моки вместо реальных API |
| `SENTRY_DSN` | _(пусто)_ | DSN для Sentry (error tracking) |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Доля трейсов для Sentry |
| `SUPERUSER_USERNAME` | _(пусто)_ | Логин суперпользователя для CI |
| `SUPERUSER_EMAIL` | _(пусто)_ | Email суперпользователя |
| `SUPERUSER_PASSWORD` | _(пусто)_ | Пароль суперпользователя |
| `GUNICORN_WORKERS` | `2` | Число воркеров gunicorn |
| `DJANGO_LOG_LEVEL` | `INFO` | Уровень логирования |

---

## Запуск на удалённом сервере

### Требования к серверу

- Ubuntu 22.04 / Debian 12
- Docker Engine 24+ и Docker Compose Plugin
- Открытые порты: **80** (HTTP), **443** (HTTPS, опционально)
- Минимум 2 ГБ RAM (Celery worker + Neo4j требуют памяти)

### 1. Установить Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

### 2. Клонировать и настроить

```bash
git clone <url> skillpath_navigator
cd skillpath_navigator
cp backend/.env.example .env
nano .env
```

Минимальные изменения для production:

```env
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(50))">
DEBUG=False
ALLOWED_HOSTS=your-server-ip,yourdomain.com

DB_NAME=skillpath_db
DB_PASSWORD=<сложный пароль>
USE_REDIS_CACHE=true
GRAPH_BACKEND=memory

SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@yourdomain.com
SUPERUSER_PASSWORD=<сложный пароль>
```

### 3. Запустить

```bash
docker compose up --build -d
```

При первом запуске `entrypoint.sh` автоматически выполняет migrate, collectstatic, create_superuser, seed_skills.

После запуска:
- **Фронтенд:** `http://your-server-ip/`
- **Admin:** `http://your-server-ip/admin/`
- **API:** `http://your-server-ip/api/v1/`
- **Swagger:** `http://your-server-ip/api/docs/`
- **Flower:** `http://your-server-ip:5555/` (мониторинг Celery)

### 4. HTTPS с Let's Encrypt

```bash
sudo apt install -y certbot
docker compose down
sudo certbot certonly --standalone -d yourdomain.com
```

Добавьте в `frontend/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    # ... остальной конфиг
}
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

### 5. Полезные команды

```bash
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose exec backend python manage.py migrate
git pull && docker compose up --build -d
docker compose down      # остановить
docker compose down -v   # остановить + удалить данные (осторожно!)
```

---

## REST API

Все эндпоинты требуют `Authorization: Bearer <access_token>`, кроме `/health/`, `/ready/` и эндпоинтов аутентификации.

### Аутентификация

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/auth/register/` | Регистрация (`username`, `email`, `password`) |
| POST | `/api/v1/auth/token/` | Получить JWT (`access` + `refresh`). Лимит: 10/час |
| POST | `/api/v1/auth/token/refresh/` | Обновить access (refresh ротируется и инвалидируется) |

### Навыки

| Метод | URL | Права | Описание |
|---|---|---|---|
| GET | `/api/v1/skills/` | все | Список (пагинация, фильтры) |
| GET | `/api/v1/skills/<id>/` | все | Детали навыка |
| POST | `/api/v1/skills/` | admin | Создать навык |
| PUT/PATCH | `/api/v1/skills/<id>/` | admin | Изменить навык |
| DELETE | `/api/v1/skills/<id>/` | admin | Удалить навык |
| GET | `/api/v1/skills/graph/` | все | Граф (узлы + рёбра), кэш 5 мин |
| GET | `/api/v1/skills/<id>/next-step/` | все | Рекомендованные следующие навыки |
| GET | `/api/v1/skills/<from>/path-to/<to>/` | все | Кратчайший путь обучения |
| GET | `/api/v1/skills/<id>/resources/` | все | Материалы (GitHub, YouTube, курсы) |
| POST | `/api/v1/skills/from-text/` | все | LLM-разбор (async, лимит 10/час) → `{task_id}` |

### Прогресс и обучение

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/progress/update/` | Обновить прогресс (`skill_id`, `completion_percent`) |
| POST | `/api/v1/learning-path/` | Построить план по `target_skills` (макс. 10) |
| GET | `/api/v1/users/<id>/path/` | Навыки и прогресс (только свои или admin) |

### Задачи (Celery)

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/tasks/<task_id>/` | Статус задачи: `{state, result}` |

`state`: `PENDING` → `STARTED` → `SUCCESS` / `FAILURE`

Фронтенд автоматически опрашивает этот эндпоинт каждые 2 секунды (до 30 попыток) после `POST /skills/from-text/`.

### Служебные

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/health/` | Liveness probe — `{"status": "ok"}` |
| GET | `/api/v1/ready/` | Readiness probe — проверяет DB и Redis |
| GET | `/metrics` | Prometheus метрики (только Docker-сеть) |
| GET | `/api/schema/` | OpenAPI 3.0 schema |
| GET | `/api/docs/` | Swagger UI |

---

## GraphQL

**Эндпоинт:** `/graphql/`
**Аутентификация:** `Authorization: Bearer <access_token>` (обязательно)
**GraphiQL:** только при `DEBUG=True`

```graphql
# Queries
users { id username email }
skills { id name level tags isVerified }
skillGraph { nodes { id name level } edges { from to type } }
nextSkills(userId: Int!) { skill level reason }
learningPath(startSkill: String!, endSkill: String!) { path distance levels }
githubRepos(skillName: String!) { name url stars }
youtubeVideos(skillName: String!) { title url }
courses(skillName: String!) { title url platform }

# Mutations
createSkill(name: String!, description: String, level: String, tags: [String])
addSkillDependency(skill: String!, dependsOn: String!, relationType: String)
ingestSkillsFromText(text: String!)
updateProgress(skillName: String!, completionPercent: Int!)
```

---

## WebSocket

**URL:** `ws://<host>/ws/progress/<user_id>/?token=<access_token>`

Коды закрытия: `4001` — невалидный токен, `4003` — чужой канал.

**Событие от сервера** (после каждого `POST /api/v1/progress/update/`):
```json
{ "skill": "Django", "completion_percent": 75 }
```

---

## Мониторинг

### Flower — Celery Dashboard

Доступен на `http://localhost:5555` (или `http://your-server-ip:5555`).

Показывает активные задачи, очереди, историю выполнения, статус воркеров.

```bash
# Запустить через docker compose (включён по умолчанию)
docker compose up flower -d

# Или локально
celery -A config flower --port=5555
```

### Prometheus

Метрики Django доступны на `/metrics` — только из Docker-сети (nginx блокирует внешний доступ). Подключайте Prometheus-scraper изнутри сети.

### Sentry

Укажите `SENTRY_DSN` в `.env` — ошибки Django, Celery и Redis будут автоматически попадать в Sentry с трейсами производительности.

---

## Тесты и линтинг

```bash
# Запустить тесты с coverage (gate 60%)
make test

# Проверить стиль
make lint

# Форматировать код
make fmt

# Установить pre-commit хуки
pip install pre-commit && pre-commit install
```

Тест-модули в `backend/tests/`:

| Файл | Что покрывает |
|---|---|
| `conftest.py` | Pytest fixtures (in-memory cache, reset между тестами) |
| `factories.py` | UserFactory, SkillFactory, UserSkillFactory |
| `test_api.py` | REST-эндпоинты, прогресс, LLM-разбор |
| `test_tasks.py` | Celery task status, rate-limit, concurrency (select_for_update) |
| `test_permissions.py` | Права доступа, пагинация, фильтры |
| `test_graph.py` | GraphService, алгоритмы пути, взвешивание |
| `test_recommendations.py` | RecommendationEngine |
| `test_graphql_schema.py` | GraphQL queries и mutations |
| `test_skills.py` | Модели Skill, UserSkill, signals |
| `test_users.py` | Регистрация, JWT-аутентификация |
| `test_progress.py` | UserSkillProgress, WebSocket broadcast |
| `test_resources.py` | GitHub, YouTube, курсы (мок) |

Покрытие: **72%** (gate: 60%).

---

## CI/CD

GitHub Actions запускается при push/PR в `main`.

| Job | Когда | Что делает |
|---|---|---|
| `test` | push + PR | pytest + coverage gate 60% (SQLite, без внешних сервисов) |
| `lint` | push + PR | black + isort + flake8 |
| `mypy` | push + PR | Type check (`--explicit-package-bases`, migrations excluded) |
| `docker-build` | push + PR | Собирает backend и frontend образы (без push) |
| `publish` | только push в `main` | Пушит в `ghcr.io/<repo>/backend:latest` и `frontend:latest` |

---

## Make-команды

```bash
make dev         # docker compose up --build (foreground)
make prod        # docker compose up --build -d (background)
make test        # pytest + coverage
make lint        # black --check + isort --check + flake8
make fmt         # black + isort (авто-форматирование)
make migrate     # python manage.py migrate
make shell       # python manage.py shell
make seed        # наполнить БД из backend/data/skills.csv
make superuser   # создать суперпользователя из .env
```
