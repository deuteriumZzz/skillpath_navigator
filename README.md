# SkillPath Navigator

Дорожная карта для программиста на Python: пользователь описывает свои навыки (в том числе свободным текстом — разбирается через LLM), система строит граф навыков и подсказывает следующие шаги обучения, проверяет, хватает ли у пользователя знаний для перехода к новому навыку, и рекомендует, где искать материалы (GitHub, YouTube, курсы).

## Архитектура

```
Student app
   │  REST (DRF) / GraphQL (graphene-django) / WebSocket (Channels) + JWT Auth
   ▼
apps.api / apps.graphql_schema / apps.progress.consumers
   │
   ├─ apps.recommendations  — Learning Path Engine: графовые алгоритмы (через apps.graph)
   │                          + LLM-разбор текстового описания навыков (Anthropic Claude)
   ├─ apps.graph             — граф навыков: Neo4j (прод) или networkx in-memory (dev/тесты)
   ├─ apps.skills / apps.users / apps.progress — PostgreSQL (или SQLite в dev)
   └─ apps.resources         — GitHub API / YouTube Data API / Course APIs (мок без ключей)

Redis — кэш (django-redis) и channel layer для WebSocket-уведомлений о прогрессе.
```

MCP (Model Context Protocol) используется как канал самого приложения к LLM: если в `MCP_SERVER_URLS` заданы адреса MCP-серверов, они подключаются к запросу Anthropic Messages API (`mcp_servers`) для обогащения контекста при разборе текста — отдельный MCP-сервер не разворачивается.

## Стек

Django 4.2 + DRF + graphene-django (GraphQL) + djangorestframework-simplejwt (JWT) + Channels (WebSocket) + Neo4j/networkx (граф) + PostgreSQL/SQLite + Redis + Anthropic Claude (LLM).

## Быстрый старт (без Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # или requirements-dev.txt для линтеров/типизации
cp .env.example ../.env                # заполнить при необходимости (ключи можно оставить пустыми — включится мок-режим)
python manage.py migrate               # без DB_NAME в .env используется SQLite
python manage.py createsuperuser        # опционально
python manage.py runserver
```

Без заданных `DB_NAME`/`NEO4J_URI`-ключей/`ANTHROPIC_API_KEY` проект всё равно полностью работает: БД — SQLite, граф навыков — in-memory (networkx), LLM-разбор текста — офлайн-эвристика, внешние интеграции — моки (`USE_MOCK_EXTERNAL_APIS=True` по умолчанию).

## Через Docker Compose (Postgres + Neo4j + Redis)

```bash
cp backend/.env.example .env   # заполнить DB_NAME/NEO4J_*/REDIS_* при необходимости
docker compose up --build
```

## Тесты

```bash
cd backend
DB_NAME= python manage.py test apps.graph.tests apps.skills.tests apps.users.tests \
    apps.progress.tests apps.recommendations.tests apps.resources.tests \
    apps.graphql_schema.tests apps.api.tests
```

(`DB_NAME=` форсирует SQLite-fallback, если Postgres не поднят локально.)

## REST API

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/token/` | Получить JWT (access/refresh) |
| POST | `/api/auth/token/refresh/` | Обновить access-токен |
| GET | `/api/skills/graph/` | Узлы и зависимости графа навыков |
| GET | `/api/skills/<id>/next-step/` | Рекомендованные следующие навыки |
| GET | `/api/skills/<from_id>/path-to/<to_id>/` | Кратчайший путь обучения между навыками |
| GET | `/api/skills/<id>/resources/` | Где искать материалы (GitHub/YouTube/курсы) |
| POST | `/api/skills/from-text/` | Разобрать текстовое описание навыков пользователя (LLM) |
| POST | `/api/progress/update/` | Обновить прогресс по навыку (`skill_id`, `completion_percent`) |
| POST | `/api/learning-path/` | Построить план обучения по `target_skills` |
| GET | `/api/users/<id>/path/` | Текущие навыки и прогресс пользователя |

## GraphQL

`/graphql/` (GraphiQL включён в DEBUG). Поддерживает те же операции через `Query`/`Mutation` (см. `apps/graphql_schema/types.py`, `mutations.py`).

## WebSocket

`ws://<host>/ws/progress/<user_id>/` — уведомления в реальном времени при обновлении прогресса (`apps/progress/consumers.py`).
