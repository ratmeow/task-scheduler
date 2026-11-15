.PHONY: test-local test-docker infra-up infra-down start-app
.PHONY: dev-infra-up dev-infra-down dev-infra-logs dev-run dev-local dev-docker
.PHONY: prod-up prod-down
.PHONY: test-infra-up test-infra-down

TEST_ARGS ?= --asyncio-mode=auto tests/

test-infra-up:
	docker compose -f compose.test.yaml --env-file test.env up -d --wait test-postgres test-redis

test-infra-down:
	docker compose -f compose.test.yaml --env-file test.env down

test-local:
	$(MAKE) test-infra-up
	trap '$(MAKE) test-infra-down' EXIT; \
	export $$(cat test.env | xargs) && pytest $(TEST_ARGS)

test-docker:
	trap '$(MAKE) test-infra-down' EXIT; \
	docker compose -f compose.test.yaml --env-file test.env run --build --rm test-backend pytest $(TEST_ARGS)

dev-infra-up:
	docker compose -f compose.dev.yaml --env-file dev.env up -d dev-postgres dev-redis

dev-down:
	docker compose -f compose.dev.yaml --env-file dev.env down

dev-run-backend:
	docker compose -f compose.dev.yaml --env-file dev.env up --build dev-backend

start-app:
	export $$(cat dev.env | xargs) && alembic upgrade head && uvicorn task_scheduler.main:create_app --host "0.0.0.0" --port 8080
