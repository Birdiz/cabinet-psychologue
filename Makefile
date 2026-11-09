# Package name: single place to change if it is renamed
# (also update APP_MODULE in the Dockerfile).
PKG        ?= cabinet
APP_MODULE ?= $(PKG).main:app
IMAGE      ?= $(PKG)

# Load .env into `uv run` only when the file exists.
ENV_FILE := $(if $(wildcard .env),--env-file .env)

.DEFAULT_GOAL := help
.PHONY: help install dev test lint fmt typecheck check preflight docker-build up watch down clean

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

## --- Local development -----------------------------------------------------

install: ## Create the venv and install all dependencies (incl. dev)
	uv sync

dev: ## Run the app with auto-reload on http://localhost:8000
	uv run $(ENV_FILE) uvicorn $(APP_MODULE) --reload

## --- Quality ---------------------------------------------------------------

test: ## Run the test suite with the coverage gate
	uv run pytest --cov

lint: ## Check lint and formatting (no changes)
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Fix lint issues and format the code
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Run the type checker
	uv run mypy

check: lint typecheck test ## Run lint, type check and tests

## --- Docker ----------------------------------------------------------------

# Fail early with a readable message when the project files the image needs
# are missing (otherwise BuildKit reports a checksum error on COPY).
PREFLIGHT_FILES := pyproject.toml uv.lock src

preflight:
	@missing=""; \
	for f in $(PREFLIGHT_FILES); do [ -e "$$f" ] || missing="$$missing $$f"; done; \
	if [ -n "$$missing" ]; then \
		echo "Missing:$$missing"; \
		echo "Run uv init --package, uv add ..., uv lock first."; \
		exit 1; \
	fi

docker-build: preflight ## Build the production image
	docker build -t $(IMAGE) .

up: preflight ## Build and run the container (reads .env if present)
	docker compose up --build

watch: preflight ## Run the container and rebuild on source changes
	docker compose watch

down: ## Stop and remove the container
	docker compose down

## --- Housekeeping ----------------------------------------------------------

clean: ## Remove caches
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
