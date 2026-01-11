.PHONY: dev shell make migrate check

dev:
	uv run python manage.py runserver

shell:
	uv run python manage.py shell

makemigrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

check:
	uv run ruff check .

check-fix:
	uv run ruff check . --fix