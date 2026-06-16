.PHONY: dev test lint fmt migrate shell

dev:
	docker compose up --build

test:
	cd backend && DB_NAME= USE_REDIS_CACHE=false python manage.py test tests --verbosity=2

lint:
	flake8 backend/ --max-line-length=119 --exclude=migrations,venv
	isort --check-only --profile black backend/
	black --check backend/

fmt:
	black backend/
	isort --profile black backend/

migrate:
	cd backend && python manage.py migrate

shell:
	cd backend && python manage.py shell
