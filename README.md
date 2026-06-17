# SkillPath Navigator

Рекомендательная система обучения для разработчиков. Пользователь описывает свои навыки (в том числе свободным текстом — разбирается через LLM), система строит граф навыков, рекомендует следующие шаги, строит оптимальный путь обучения и подсказывает где искать материалы.

## Содержание

- [Стек](#стек)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Docker Compose](#docker-compose)
- [REST API](#rest-api)
- [GraphQL](#graphql)
- [WebSocket](#websocket)
- [Тесты](#тесты)
- [Разработка](#разработка)

---

## Стек

| Слой | Технологии |
|---|---|
| Фреймворк | Django 4.2, Django REST Framework 3.14 |
| Аутентификация | JWT (djangorestframework-simplejwt), Argon2 |
| API | REST (DRF) + GraphQL (graphene-django) |
| Real-time | Django Channels 4 + WebSocket |
| Граф навыков | Neo4j 5 (прод) / networkx in-memory (dev/тесты) |
| База данных | PostgreSQL 15 / SQLite (dev/тесты) |
| Кэш | Redis 7 (django-redis) |
| LLM | Anthropic Claude (с поддержкой MCP) |
| Внешние API | GitHub, YouTube, Stepik, Coursera (мок без ключей) |
| Документация | drf-spectacular (OpenAPI 3.0 + Swagger UI) |

---

## Архитектура

```
Клиент
  │  REST /api/v1/  ·  GraphQL /graphql/  ·  WebSocket ws://.../ws/progress/<id>/
  ▼
┌─────────────────────────────────────────────────────┐
│  apps.api          — REST views, permissions, filters│
│  apps.graphql_schema — GraphQL schema + mutations    │
│  apps.progress.consumers — WebSocket consumer (JWT) │
└──────────────────────────┬──────────────────────────┘
                           │
          ┌────────────────┼───────────────────┐
          ▼                ▼                   ▼
   apps.recommendations  apps.graph      apps.resources
   RecommendationEngine  GraphService    GitHub / YouTube
   SkillTextAnalyzer     Neo4j / networkx Stepik / Coursera
   (Anthropic Claude)
          │
          ▼
   apps.skills / apps.users / apps.progress
   PostgreSQL (или SQLite в dev)

Redis — кэш графа навыков + channel layer для WebSocket

core/
  constants.py  — SKILL_LEVELS, LEVEL_CHOICES, RELATION_TYPES, кэш-ключи
  middleware.py — JWTAuthMiddleware для WebSocket
  pagination.py — StandardPagination (page_size=20, max=100)
  permissions.py — IsAdminOrReadOnly, IsOwnerOrAdmin
```

**MCP:** если в `MCP_SERVER_URLS` заданы адреса MCP-серверов, они передаются в Anthropic Messages API при разборе текста — отдельный MCP-сервер разворачивать не нужно.

---

## Быстрый старт

### Без Docker (SQLite + in-memory граф)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example ../.env          # при необходимости заполнить ключи
python manage.py migrate
python manage.py runserver
```

Без `DB_NAME`, `NEO4J_*`, `ANTHROPIC_API_KEY` проект работает полностью:
- БД → SQLite
- Граф → in-memory (networkx)
- LLM-разбор текста → офлайн-эвристика
- Внешние API → моки (`USE_MOCK_EXTERNAL_APIS=True`)

### Создание суперпользователя

Интерактивно:
```bash
python manage.py createsuperuser
```

Для CI / Docker (через переменные окружения):
```bash
SUPERUSER_USERNAME=admin SUPERUSER_EMAIL=admin@example.com SUPERUSER_PASSWORD=changeme \
    python manage.py create_superuser
```

Команда идемпотентна — при повторном запуске ничего не пересоздаёт.

---

## Docker Compose

Поднимает PostgreSQL 15, Neo4j 5, Redis 7 и Django-приложение:

```bash
cp backend/.env.example .env   # заполнить DB_NAME, NEO4J_PASSWORD и др.
docker compose up --build
```

Сервисы:

| Сервис | Порт | Назначение |
|---|---|---|
| backend | 8000 | Django + ASGI (Channels) |
| postgres | 5432 | Основная БД |
| neo4j | 7474, 7687 | Граф навыков |
| redis | 6379 | Кэш + WebSocket channel layer |

---

## REST API

Все эндпоинты требуют заголовок `Authorization: Bearer <access_token>`, кроме `/api/v1/health/` и эндпоинтов аутентификации.

### Аутентификация

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/auth/register/` | Регистрация (`username`, `email`, `password`) |
| POST | `/api/v1/auth/token/` | Получить JWT (`access` + `refresh`) |
| POST | `/api/v1/auth/token/refresh/` | Обновить access-токен (refresh ротируется) |

### Навыки

| Метод | URL | Права | Описание |
|---|---|---|---|
| GET | `/api/v1/skills/` | все | Список навыков (пагинация, фильтры) |
| GET | `/api/v1/skills/<id>/` | все | Детали навыка |
| POST | `/api/v1/skills/` | admin | Создать навык |
| PUT/PATCH | `/api/v1/skills/<id>/` | admin | Изменить навык |
| DELETE | `/api/v1/skills/<id>/` | admin | Удалить навык |
| GET | `/api/v1/skills/graph/` | все | Граф навыков (узлы + рёбра), кэш 5 мин |
| GET | `/api/v1/skills/<id>/next-step/` | все | Рекомендованные следующие навыки |
| GET | `/api/v1/skills/<from>/path-to/<to>/` | все | Кратчайший путь обучения |
| GET | `/api/v1/skills/<id>/resources/` | все | Материалы (GitHub, YouTube, курсы) |
| POST | `/api/v1/skills/from-text/` | все | Разобрать описание навыков через LLM |

**Фильтры для `/api/v1/skills/`:**

| Параметр | Описание | Пример |
|---|---|---|
| `level` | Уровень сложности | `?level=beginner` |
| `is_verified` | Только проверенные | `?is_verified=true` |
| `name` | Подстрока в названии | `?name=python` |
| `tag` | Тег | `?tag=backend` |
| `search` | Полнотекстовый поиск | `?search=django` |
| `ordering` | Сортировка | `?ordering=-created_at` |
| `page_size` | Размер страницы (макс. 100) | `?page_size=10` |

Допустимые значения `level`: `beginner`, `intermediate`, `advanced`, `expert`.

### Прогресс и обучение

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/progress/update/` | Обновить прогресс (`skill_id`, `completion_percent`) |
| POST | `/api/v1/learning-path/` | Построить план по `target_skills` |
| GET | `/api/v1/users/<id>/path/` | Навыки и прогресс пользователя (только свои или admin) |

### Прочее

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/health/` | Liveness probe — `{"status": "ok"}`, без авторизации |
| GET | `/api/schema/` | OpenAPI 3.0 schema (JSON) |
| GET | `/api/docs/` | Swagger UI |

---

## GraphQL

**Эндпоинт:** `/graphql/`  
**Аутентификация:** `Authorization: Bearer <access_token>` (обязательно)  
**GraphiQL:** доступен только при `DEBUG=True`

### Queries

```graphql
users { id username email }
skills { id name level tags isVerified }
skillGraph { nodes { id name level } edges { from to type } }
nextSkills(userId: Int!) { skill level reason }
learningPath(startSkill: String!, endSkill: String!) { path distance levels }
githubRepos(skillName: String!) { name url stars }
youtubeVideos(skillName: String!) { title url }
courses(skillName: String!) { title url platform }
```

### Mutations

```graphql
createSkill(name: String!, description: String, level: String, tags: [String])
addSkillDependency(skill: String!, dependsOn: String!, relationType: String)
ingestSkillsFromText(text: String!)
updateProgress(skillName: String!, completionPercent: Int!)
```

---

## WebSocket

**URL:** `ws://<host>/ws/progress/<user_id>/?token=<access_token>`

JWT передаётся в query-параметре `token`. Соединение закрывается с кодом:
- `4001` — токен отсутствует или невалиден
- `4003` — попытка подписаться на чужой прогресс

**Событие от сервера:**
```json
{ "skill": "Django", "completion_percent": 75 }
```

Событие приходит после каждого `POST /api/v1/progress/update/`.

---

## Тесты

```bash
# Через make (рекомендуется)
make test

# Напрямую (SQLite + in-memory граф, без Redis)
cd backend && DB_NAME= USE_REDIS_CACHE=false python manage.py test tests --verbosity=2
```

Тест-модули в `backend/tests/`:

| Файл | Что покрывает |
|---|---|
| `test_api.py` | REST-эндпоинты, прогресс, LLM-разбор |
| `test_permissions.py` | Права доступа, владение ресурсами, пагинация, фильтры |
| `test_graph.py` | GraphService, алгоритмы поиска пути, взвешивание |
| `test_recommendations.py` | RecommendationEngine, следующие навыки, готовность |
| `test_graphql_schema.py` | GraphQL queries и mutations |
| `test_skills.py` | Модели Skill, UserSkill, сигналы |
| `test_users.py` | Регистрация, JWT-аутентификация |
| `test_progress.py` | UserSkillProgress, сериализаторы, broadcast |
| `test_resources.py` | GitHub, YouTube, курсы (мок) |

---

## Разработка

### Переменные окружения

Скопируйте `backend/.env.example` в `.env` и заполните нужные значения.
Ключи можно оставить пустыми — включится мок-режим.

### Makefile

```bash
make dev      # docker compose up --build
make test     # запустить тесты (SQLite + in-memory)
make lint     # flake8 + isort + black (проверка)
make fmt      # black + isort (форматирование)
make migrate  # python manage.py migrate
make shell    # python manage.py shell
```

### pre-commit

```bash
pip install pre-commit
pre-commit install           # установить git-хуки
pre-commit run --all-files   # проверить всё вручную
```

Хуки: `black`, `isort`, `flake8`, `trailing-whitespace`, `debug-statements`.

### CI

GitHub Actions запускает два job'а при каждом push/PR в `main`:
- **Tests** — `python manage.py test tests` (SQLite, без Redis/Neo4j)
- **Lint** — black + isort + flake8

---

## Структура проекта

```
skillpath_navigator/
├── .github/workflows/ci.yml   # CI/CD
├── .pre-commit-config.yaml    # pre-commit хуки
├── Makefile                   # команды разработки
├── docker-compose.yml
└── backend/
    ├── config/
    │   ├── settings.py        # конфигурация
    │   ├── urls.py            # корневой роутинг (/api/v1/, /graphql/, /admin/)
    │   └── asgi.py            # ASGI + WebSocket роутинг
    ├── core/
    │   ├── constants.py       # SKILL_LEVELS, LEVEL_CHOICES, RELATION_TYPES
    │   ├── middleware.py      # JWTAuthMiddleware для WebSocket
    │   ├── pagination.py      # StandardPagination
    │   └── permissions.py     # IsAdminOrReadOnly, IsOwnerOrAdmin
    ├── apps/
    │   ├── users/             # User model, JWT auth, registration
    │   ├── skills/            # Skill, UserSkill models + filters
    │   ├── graph/             # GraphService, Neo4j/networkx backends
    │   ├── progress/          # UserSkillProgress, WebSocket consumer
    │   ├── recommendations/   # RecommendationEngine, SkillTextAnalyzer (LLM)
    │   ├── resources/         # GitHub, YouTube, Stepik, Coursera
    │   ├── api/               # REST views, URLs
    │   └── graphql_schema/    # GraphQL schema, types, mutations
    ├── tests/                 # тесты (один файл на приложение)
    ├── requirements.txt
    └── .env.example
```
