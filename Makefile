.PHONY: install lint type test check fmt compose-up compose-down clean

install:
	uv sync --all-packages

CODE = libs services mcp-gateway

lint:
	uv run ruff check $(CODE)

fmt:
	uv run ruff check --fix $(CODE)
	uv run ruff format $(CODE)

type:
	uv run mypy -p platform_common -p contracts -p service_kit -p jobs -p persistence \
		-p real_estate_svc -p hospitals_svc -p schools_svc -p decision_svc -p mcp_gateway

test:
	uv run pytest -q

check: lint type test

compose-up:
	docker compose -f deploy/compose/docker-compose.yml up --build

compose-down:
	docker compose -f deploy/compose/docker-compose.yml down -v

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
