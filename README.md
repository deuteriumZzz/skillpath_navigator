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
- [Тесты и линтинг](#тесты-и-линтинг)
- [CI/CD](#cicd)
- [Make-команды](#make-команды)

---

## Стек

| Слой | Технологии |
|---|---|
| Фреймворк | Django 4.2, Django REST Framework 3.14 |
| Аутентификация | JWT (djangorestframework-simplejwt), Argon2 |
| API | REST (DRF) + GraphQL (graphene-django) |
| Real-time | Django Channels 4 + WebSocket |
| ASGI-сервер | Gunicorn + Uvicorn workers |
| Граф навыков | Neo4j 5 (прод) / networkx in-memory (dev/тесты) |
| База данных | PostgreSQL 15 / SQLite (dev/тесты) |
| Кэш | Redis 7 (django-redis) |
| LLM | Anthropic Claude (с поддержкой MCP) |
| Внешние API | GitHub, YouTube, Stepik, Coursera (мок без ключей) |
| Документация | drf-spectacular (OpenAPI 3.0 + Swagger UI) |
| Фронтенд | React 18 + Vite + Tailwind CSS + vis-network |
| Прокси | nginx (reverse proxy + раздача статики фронтенда) |

---

## Архитектура

```
Браузер
  │
  ▼
┌─────────────────────────────────┐
│  nginx (порт 80 / 443)          │
│  /           → React SPA        │
│  /api/       → gunicorn :8000   │
│  /admin/     → gunicorn :8000   │
│  /graphql/   → gunicorn :8000   │
│  /ws/        → gunicorn :8000   │
└────────────────┬────────────────┘
                 │
  ┌──────────────▼──────────────────────────────────┐
  │  Gunicorn + UvicornWorker (ASGI)                │
  │  apps.api          — REST (DRF)                 │
  │  apps.graphql_schema — GraphQL                  │
  │  apps.progress.consumers — WebSocket (Channels) │
  └───────────┬────────────────────┬────────────────┘
              │                    │
  ┌───────────▼──────┐  ┌─────────▼──────────────┐
  │  PostgreSQL 15   │  │  Redis 7               │
  │  (основная БД)   │  │  кэш + channel layer   │
  └──────────────────┘  └────────────────────────┘
              │
  ┌───────────▼──────┐
  │  Neo4j 5         │  ← опционально (--profile neo4j)
  │  (граф навыков)  │    по умолчанию: networkx in-memory
  └──────────────────┘

core/
  constants.py  — SKILL_LEVELS, RELATION_TYPES, ключи кэша
  middleware.py — JWTAuthMiddleware для WebSocket
  pagination.py — StandardPagination (20 / макс. 100)
  permissions.py — IsAdminOrReadOnly, IsOwnerOrAdmin
```

---

## Структура проекта

```
skillpath_navigator/
├── .github/
│   └── workflows/
│       └── ci.yml             # тесты → линтинг → docker build → push ghcr.io
├── .pre-commit-config.yaml    # black, isort, flake8
├── Makefile                   # dev, prod, test, lint, fmt, seed, superuser…
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh          # migrate → collectstatic → superuser → seed → gunicorn
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   ├── core/                  # общие утилиты (constants, middleware, pagination, permissions)
│   ├── apps/
│   │   ├── users/
│   │   ├── skills/
│   │   ├── graph/
│   │   ├── progress/
│   │   ├── recommendations/
│   │   ├── resources/
│   │   ├── api/
│   │   └── graphql_schema/
│   ├── data/
│   │   ├── skills.csv         # каталог навыков (редактируется без изменения кода)
│   │   └── dependencies.csv   # граф зависимостей
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── Dockerfile             # multi-stage: node build → nginx
    ├── nginx.conf             # конфиг nginx для контейнера
    ├── package.json
    ├── vite.config.js         # proxy /api → localhost:8000
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/
            ├── Auth.jsx
            ├── Dashboard.jsx
            ├── SkillGraph.jsx
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

Самый быстрый способ запустить проект без каких-либо зависимостей.

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

# 6. Наполнить каталог навыков (24 навыка + граф зависимостей)
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

Используется в ежедневной разработке: инфраструктура в контейнерах, Django — с горячей перезагрузкой.

```bash
# Поднять только инфраструктуру
docker compose up postgres redis -d

# Настроить .env для PostgreSQL и Redis
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
| `GRAPH_BACKEND` | `memory` | `memory` или `neo4j` |
| `NEO4J_URI` | `bolt://localhost:7687` | Адрес Neo4j |
| `NEO4J_PASSWORD` | `password` | Пароль Neo4j |
| `REDIS_HOST` | `localhost` | Хост Redis |
| `USE_REDIS_CACHE` | `True` | `false` для тестов без Redis |
| `ANTHROPIC_API_KEY` | _(пусто)_ | Ключ Claude API |
| `GITHUB_TOKEN` | _(пусто)_ | Токен GitHub API |
| `YOUTUBE_API_KEY` | _(пусто)_ | Ключ YouTube Data API |
| `STEPIK_TOKEN` | _(пусто)_ | Токен Stepik API |
| `USE_MOCK_EXTERNAL_APIS` | `True` | Моки вместо реальных API |
| `SUPERUSER_USERNAME` | _(пусто)_ | Логин суперпользователя для CI |
| `SUPERUSER_EMAIL` | _(пусто)_ | Email суперпользователя |
| `SUPERUSER_PASSWORD` | _(пусто)_ | Пароль суперпользователя |
| `GUNICORN_WORKERS` | `2` | Число воркеров gunicorn |
| `DJANGO_LOG_LEVEL` | `INFO` | Уровень логирования |

---

## Запуск на удалённом сервере

### Требования к серверу

- Ubuntu 22.04 / Debian 12 (или любой Linux с systemd)
- Docker Engine 24+ и Docker Compose Plugin
- Открытые порты: **80** (HTTP), **443** (HTTPS, опционально)
- Минимум 1 ГБ RAM (рекомендуется 2 ГБ)

### 1. Установить Docker на сервере

```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Проверить
docker --version
docker compose version
```

### 2. Скопировать проект на сервер

```bash
# С локальной машины
scp -r skillpath_navigator/ user@your-server-ip:~/

# Или клонировать напрямую на сервере
ssh user@your-server-ip
git clone <url> skillpath_navigator
cd skillpath_navigator
```

### 3. Создать и заполнить `.env`

```bash
cp backend/.env.example .env
nano .env
```

Минимально необходимые изменения для production:

```env
# ОБЯЗАТЕЛЬНО — сгенерировать случайный ключ
SECRET_KEY=<вывод: python -c "import secrets; print(secrets.token_hex(50))">
DEBUG=False
ALLOWED_HOSTS=your-server-ip,yourdomain.com

# База данных
DB_NAME=skillpath_db
DB_USER=postgres
DB_PASSWORD=<придумать сложный пароль>

# Redis
USE_REDIS_CACHE=true

# Граф (memory — без Neo4j, neo4j — с Neo4j)
GRAPH_BACKEND=memory

# Суперпользователь — создаётся автоматически при первом запуске
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@yourdomain.com
SUPERUSER_PASSWORD=<придумать сложный пароль>

# Внешние API (опционально)
GITHUB_TOKEN=
YOUTUBE_API_KEY=
USE_MOCK_EXTERNAL_APIS=True
```

### 4. Запустить в production-режиме

```bash
# Собрать образы и запустить все контейнеры в фоне
make prod
# или напрямую:
docker compose up --build -d
```

При первом запуске `entrypoint.sh` автоматически выполняет:
1. `python manage.py migrate` — применяет миграции
2. `python manage.py collectstatic` — собирает статику
3. `python manage.py create_superuser` — создаёт суперпользователя (из `.env`)
4. `python manage.py seed_skills` — наполняет каталог навыков из CSV

После запуска:
- **Фронтенд:** `http://your-server-ip/`
- **Admin:** `http://your-server-ip/admin/`
- **API:** `http://your-server-ip/api/v1/`
- **Swagger:** `http://your-server-ip/api/docs/`

### 5. Настроить HTTPS с Let's Encrypt (рекомендуется)

```bash
# Установить Certbot
sudo apt install -y certbot

# Остановить контейнеры (нужен порт 80)
docker compose down

# Получить сертификат
sudo certbot certonly --standalone -d yourdomain.com

# Сертификаты будут в:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Добавьте в `frontend/nginx.conf` блок для HTTPS и пробросьте порт 443 в `docker-compose.yml`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    # ... остальной конфиг без изменений
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}
```

```yaml
# docker-compose.yml — добавить в frontend:
ports:
  - "80:80"
  - "443:443"
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

```bash
docker compose up --build -d
```

### 6. Полезные команды после деплоя

```bash
# Просмотр логов
docker compose logs -f backend
docker compose logs -f frontend

# Войти в контейнер бэкенда
docker compose exec backend sh

# Применить новые миграции после обновления кода
docker compose exec backend python manage.py migrate

# Пересеять данные из CSV (если обновили skills.csv)
docker compose exec backend python manage.py seed_skills

# Перезапустить только бэкенд после обновления кода
git pull
docker compose up --build -d backend

# Остановить всё
docker compose down

# Остановить и удалить данные (осторожно — удаляет volumes с БД!)
docker compose down -v
```

### 7. Обновление проекта

```bash
ssh user@your-server-ip
cd skillpath_navigator

git pull origin main

# Пересобрать и перезапустить
docker compose up --build -d

# Проверить статус
docker compose ps
```

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
| `level` | Уровень: `beginner` / `intermediate` / `advanced` / `expert` | `?level=beginner` |
| `is_verified` | Только проверенные | `?is_verified=true` |
| `name` | Подстрока в названии (без учёта регистра) | `?name=python` |
| `tag` | Тег | `?tag=backend` |
| `search` | Полнотекстовый поиск по name + description | `?search=django` |
| `ordering` | Сортировка (`name`, `level`, `created_at`) | `?ordering=-created_at` |
| `page_size` | Размер страницы (макс. 100) | `?page_size=10` |

### Прогресс и обучение

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/v1/progress/update/` | Обновить прогресс (`skill_id`, `completion_percent`) |
| POST | `/api/v1/learning-path/` | Построить план по `target_skills` |
| GET | `/api/v1/users/<id>/path/` | Навыки и прогресс пользователя (только свои или admin) |

### Служебные

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

JWT передаётся в query-параметре `token`. Соединение закрывается с кодом:
- `4001` — токен отсутствует или невалиден
- `4003` — попытка подписаться на чужой прогресс

**Событие от сервера:**
```json
{ "skill": "Django", "completion_percent": 75 }
```

Событие приходит после каждого `POST /api/v1/progress/update/`.

---

## Тесты и линтинг

```bash
# Запустить все тесты (SQLite + in-memory граф, без Redis/Neo4j)
make test

# Проверить стиль кода
make lint

# Форматировать код автоматически
make fmt

# Установить pre-commit хуки (запускаются при каждом git commit)
pip install pre-commit
pre-commit install
```

Тест-модули в `backend/tests/`:

| Файл | Что покрывает |
|---|---|
| `test_api.py` | REST-эндпоинты, прогресс, LLM-разбор |
| `test_permissions.py` | Права доступа, владение ресурсами, пагинация, фильтры |
| `test_graph.py` | GraphService, алгоритмы поиска пути, взвешивание |
| `test_recommendations.py` | RecommendationEngine, следующие навыки, готовность |
| `test_graphql_schema.py` | GraphQL queries и mutations |
| `test_skills.py` | Модели Skill, UserSkill |
| `test_users.py` | Регистрация, JWT-аутентификация |
| `test_progress.py` | UserSkillProgress, сериализаторы, broadcast |
| `test_resources.py` | GitHub, YouTube, курсы (мок) |

---

## CI/CD

GitHub Actions автоматически запускается при push/PR в `main`.

| Job | Когда | Что делает |
|---|---|---|
| `test` | push + PR | Запускает тесты (SQLite, без внешних сервисов) |
| `lint` | push + PR | black + isort + flake8 |
| `docker-build` | push + PR | Собирает backend и frontend образы (без push) |
| `publish` | только push в `main` | Пушит образы в `ghcr.io/<repo>/backend:latest` и `frontend:latest` |

Образы публикуются в GitHub Container Registry автоматически — токен не нужен, используется встроенный `GITHUB_TOKEN`.

---

## Make-команды

```bash
make dev         # docker compose up --build (foreground)
make prod        # docker compose up --build -d (background, production)
make test        # запустить тесты (SQLite + in-memory)
make lint        # проверить стиль кода
make fmt         # отформатировать код (black + isort)
make migrate     # python manage.py migrate
make shell       # python manage.py shell
make seed        # наполнить БД из backend/data/skills.csv
make superuser   # создать суперпользователя из .env
```
