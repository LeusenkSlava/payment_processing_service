# Shell / Make config
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

.SILENT:
MAKEFLAGS += --no-print-directory

# -----------------------------
# User-configurable variables (edit this)
# INFRA_SERVICES: long-running infra (db, broker, cache, ...)
# INFRA_INIT_SERVICES: one-shot services that prepare INFRA_SERVICES
# MIGRATION_DB_SERVICE: transactional db service used by alembic (empty = no migrations)
# STAIRWAY_TEST: path to stairway test (empty = skip stairway step)
# -----------------------------
PROJECT_NAME ?= $(notdir $(abspath .))

# -----------------------------
# Internal vars / aliases
# -----------------------------
DOCKER_COMPOSE := docker compose -p $(PROJECT_NAME)
DOCKER_ENV := scripts/makefile/docker_env.sh
DOCKER_PRUNE := scripts/makefile/docker_prune.sh

# Docker compose
.PHONY: docker-env upd up down stop
docker-env:
	$(DOCKER_ENV)

upd: docker-env
	$(DOCKER_COMPOSE) up -d --build --force-recreate

up: docker-env
	$(DOCKER_COMPOSE) up --build --force-recreate

just_up: docker-env
	$(DOCKER_COMPOSE) up -d

start: docker-env
	$(DOCKER_COMPOSE) start

restart: docker-env
	$(DOCKER_COMPOSE) restart

down:
	$(DOCKER_COMPOSE) down

stop:
	$(DOCKER_COMPOSE) stop

.PHONY: prune
prune:
	$(DOCKER_PRUNE)

.PHONY: migration
migration: docker-env
	@if [ -z "$(m)" ]; then \
		echo "Ошибка: Укажите описание миграции. Пример: make migration m=\"Add novels model\""; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec app alembic revision --autogenerate -m "$(m)"

# Logs
.PHONY: logs logs-app logs-consumer logs-migrations logs-db logs-rabbitmq
logs:
	$(DOCKER_COMPOSE) logs -f --tail=200

logs-app:
	$(DOCKER_COMPOSE) logs -f --tail=200 app

logs-consumer:
	$(DOCKER_COMPOSE) logs -f --tail=200 consumer

logs-migrations:
	$(DOCKER_COMPOSE) logs --tail=200 migrations

logs-db:
	$(DOCKER_COMPOSE) logs -f --tail=200 db_pg

logs-rabbitmq:
	$(DOCKER_COMPOSE) logs -f --tail=200 rabbitmq

# Status
.PHONY: ps
ps:
	$(DOCKER_COMPOSE) ps
