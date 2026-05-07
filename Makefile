.PHONY: dev test lint docker-up docker-down clean

PYTHON = python
PIP = pip
DOCKER_COMPOSE = docker-compose

dev:
	$(PYTHON) aegis/interfaces/cli.py

test:
	pytest tests/

lint:
	black aegis/ tests/
	ruff check aegis/ tests/
	mypy aegis/

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
