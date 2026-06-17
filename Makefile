.PHONY: dev prod test lint fmt migrate shell seed superuser

# Разработка (поднимает postgres + redis + neo4j через docker, Django запускается локально)
dev:
	docker compose up --build

# Продакшен (всё в docker, frontend на порту 80)
prod:
	docker compose up --build -d

# Запустить тесты (SQLite + in-memory граф, без Redis/Neo4j)
test:
	cd backend && DB_NAME= USE_REDIS_CACHE=false GRAPH_BACKEND=memory python manage.py test tests --verbosity=2

# Проверить стиль кода
lint:
	flake8 backend/ --max-line-length=119 --exclude=migrations,venv
	isort --check-only --profile black backend/
	black --check backend/

# Форматировать код
fmt:
	black backend/
	isort --profile black backend/

# Применить миграции
migrate:
	cd backend && python manage.py migrate

# Django shell
shell:
	cd backend && python manage.py shell

# Наполнить БД навыками из backend/data/skills.csv и backend/data/dependencies.csv
seed:
	cd backend && python manage.py seed_skills

# Создать суперпользователя (использует SUPERUSER_* из .env)
superuser:
	cd backend && python manage.py create_superuser
